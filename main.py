from flask import Flask, render_template, request, jsonify, session
import openai
import os
import logging
import uuid
import time
import re
from datetime import datetime

from models import db, Conversation, Message, FAQ, AnalyticsLog

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# System prompt for the AI support bot
SYSTEM_PROMPT = """
You are a helpful, friendly customer support assistant. 
Your job is to provide clear, concise, and accurate information to customer queries.
Be polite, professional, and empathetic in your responses.
If you don't know the answer to a question, be honest about it instead of making something up.
"""

# Create a function to initialize the database data
def init_database_data():
    """Initialize database with sample data"""
    # Add some sample FAQs if none exist
    if FAQ.query.count() == 0:
        sample_faqs = [
            FAQ(
                question="What is this support bot?",
                answer="This is an AI-powered support bot designed to answer your questions and provide assistance.",
                keywords="support,bot,help,assistant,what,is",
                category="General"
            ),
            FAQ(
                question="How do I reset my password?",
                answer="To reset your password, click on the 'Forgot Password' link on the login page and follow the instructions sent to your email.",
                keywords="reset,password,forgot,login,credentials",
                category="Account"
            ),
            FAQ(
                question="Do you offer refunds?",
                answer="Yes, we offer refunds within 30 days of purchase if you're not satisfied with our product. Please contact our support team with your order number for assistance.",
                keywords="refund,return,money,back,purchase",
                category="Billing"
            )
        ]
        db.session.add_all(sample_faqs)
        db.session.commit()

def get_session_id():
    """Get or create a session ID for the current user"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_or_create_conversation(session_id):
    """Get existing conversation or create a new one for this session"""
    conversation = Conversation.query.filter_by(session_id=session_id).first()
    if not conversation:
        conversation = Conversation(session_id=session_id)
        db.session.add(conversation)
        db.session.commit()
    return conversation

def log_interaction(conversation_id, user_query, bot_response, response_time):
    """Log interaction for analytics"""
    log_entry = AnalyticsLog(
        conversation_id=conversation_id,
        user_query=user_query,
        bot_response=bot_response,
        response_time=response_time,
        ip_address=request.remote_addr
    )
    db.session.add(log_entry)
    db.session.commit()

def find_matching_faq(query, threshold=0.7):
    """Find matching FAQ for the query if one exists"""
    # This is a simple keyword matching approach
    # In a production app, you might want to use something more sophisticated like embeddings
    
    # Normalize the query: lowercase and remove punctuation
    normalized_query = re.sub(r'[^\w\s]', '', query.lower())
    words = set(normalized_query.split())
    
    # Get all FAQs
    faqs = FAQ.query.all()
    best_match = None
    best_score = 0
    
    for faq in faqs:
        if not faq.keywords:
            continue
            
        # Get keywords from the FAQ
        faq_keywords = set(faq.keywords.lower().split(','))
        
        # Calculate match score (simple word overlap)
        matches = words.intersection(faq_keywords)
        if not matches:
            continue
            
        score = len(matches) / max(len(words), len(faq_keywords))
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = faq
    
    return best_match

def get_conversation_history(conversation_id, max_messages=10):
    """Get the recent conversation history"""
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.desc()).limit(max_messages).all()
    # Reverse to get chronological order
    messages.reverse()
    
    # Format for OpenAI API
    formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for message in messages:
        role = "user" if message.is_user else "assistant"
        formatted_messages.append({"role": role, "content": message.content})
    
    return formatted_messages

@app.route("/")
def home():
    """Render the chat interface"""
    # Ensure we have a session ID
    session_id = get_session_id()
    # Get or create conversation for this session
    conversation = get_or_create_conversation(session_id)
    
    # Get the last few messages to display on page load
    recent_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.desc()).limit(5).all()
    recent_messages.reverse()  # Display in chronological order
    
    return render_template("index.html", messages=recent_messages)

@app.route("/chat", methods=["POST"])
def chat():
    """Process chat messages and get AI responses"""
    start_time = time.time()
    
    data = request.json
    user_input = data.get("message", "")
    
    logger.debug(f"Received message: {user_input}")
    
    # Get session and conversation
    session_id = get_session_id()
    conversation = get_or_create_conversation(session_id)
    
    if not user_input.strip():
        return jsonify({"reply": "Please enter a message."})
    
    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        content=user_input,
        is_user=True
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Check for FAQ match first
    matching_faq = find_matching_faq(user_input)
    if matching_faq:
        logger.info(f"Found matching FAQ: {matching_faq.question}")
        answer = matching_faq.answer
    else:
        try:
            # Get conversation history for context
            messages = get_conversation_history(conversation.id)
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            answer = response.choices[0].message.content.strip()
            logger.debug(f"AI response: {answer[:50]}...")  # Log first 50 chars of response
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            return jsonify({"reply": f"An error occurred: {str(e)}"}), 500
    
    # Store bot response
    bot_message = Message(
        conversation_id=conversation.id,
        content=answer,
        is_user=False
    )
    db.session.add(bot_message)
    
    # Update conversation last updated time
    conversation.last_updated = datetime.utcnow()
    db.session.commit()
    
    # Calculate response time and log interaction
    response_time = time.time() - start_time
    log_interaction(conversation.id, user_input, answer, response_time)
    
    return jsonify({"reply": answer})

@app.route("/faqs")
def list_faqs():
    """Admin page to view FAQs"""
    faqs = FAQ.query.all()
    return render_template("faqs.html", faqs=faqs)

@app.route("/analytics")
def analytics_dashboard():
    """Simple analytics dashboard"""
    # Get total number of conversations
    conversation_count = Conversation.query.count()
    
    # Get total number of messages
    message_count = Message.query.count()
    
    # Get average response time
    avg_response_time = db.session.query(db.func.avg(AnalyticsLog.response_time)).scalar() or 0
    
    # Get recent logs
    recent_logs = AnalyticsLog.query.order_by(AnalyticsLog.timestamp.desc()).limit(10).all()
    
    return render_template(
        "analytics.html", 
        conversation_count=conversation_count,
        message_count=message_count,
        avg_response_time=avg_response_time,
        recent_logs=recent_logs
    )

with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    # Initialize sample data
    init_database_data()

if __name__ == "__main__":
    # Run the server on port 5000 with host 0.0.0.0 (accessible from outside)
    app.run(host="0.0.0.0", port=5000, debug=True)
