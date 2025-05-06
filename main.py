from flask import Flask, render_template, request, jsonify, session
import openai
import os
import logging
import time
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from uuid import uuid4

from knowledge_base_handler import KnowledgeBaseHandler
from token_utils import count_tokens, log_message

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

# Setup SQLAlchemy
db = SQLAlchemy(app)

# Initialize knowledge base handler
kb_handler = KnowledgeBaseHandler(openai_api_key=openai_api_key)

# Default model to use for OpenAI API calls
DEFAULT_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.

# System prompt for the AI support bot
SYSTEM_PROMPT = """
You are a helpful, friendly customer support assistant. 
Your job is to provide clear, concise, and accurate information to customer queries.
Be polite, professional, and empathetic in your responses.
Always prioritize information from the knowledge base when available.
If the knowledge base provides information relevant to the query, use that information in your response.
If you don't know the answer to a question and it's not in the knowledge base, be honest about it instead of making something up.
"""

# Initialize knowledge base on startup
try:
    logger.info("Loading knowledge base on startup...")
    kb_handler.load_knowledge_base()
    logger.info("Knowledge base loaded successfully")
except Exception as e:
    logger.error(f"Error loading knowledge base: {str(e)}")

@app.route("/")
def home():
    """Render the chat interface"""
    return render_template("index.html")

@app.route("/get_history", methods=["GET"])
def get_history():
    """Get the conversation history for the current session"""
    try:
        current_session_id = session.get('session_id')
        if not current_session_id:
            # Create a new session if none exists
            session['session_id'] = generate_session_id()
            current_session_id = session['session_id']
            logger.info(f"Created new session with ID: {current_session_id}")
            return jsonify({"messages": []})
            
        # Get session
        chat_session = Session.query.filter_by(session_id=current_session_id).first()
        if not chat_session:
            logger.warning(f"No session found with ID: {current_session_id}")
            return jsonify({"messages": []})
            
        # Get messages for this session
        messages = Message.query.filter_by(
            session_id=chat_session.id
        ).order_by(Message.timestamp).all()
        
        # Format messages for the frontend
        formatted_messages = []
        for msg in messages:
            message_data = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            }
            
            # Add sources if available
            if msg.sources:
                try:
                    message_data["sources"] = json.loads(msg.sources)
                except:
                    message_data["sources"] = []
                    
            formatted_messages.append(message_data)
            
        return jsonify({"messages": formatted_messages})
        
    except Exception as e:
        error_msg = f"Error retrieving conversation history: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

# Import the models at the top after db initialization
from models import Session, Message, generate_session_id

# Initialize a session on app startup or restore an existing one
@app.before_request
def setup_session():
    """Ensure a valid session exists"""
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
        logger.info(f"Created new session with ID: {session['session_id']}")
    else:
        logger.debug(f"Using existing session: {session['session_id']}")

def get_conversation_history(session_id, limit=10):
    """Get the conversation history from the database for a given session"""
    try:
        # Get the session object
        chat_session = Session.query.filter_by(session_id=session_id).first()
        if not chat_session:
            logger.warning(f"No session found with ID: {session_id}")
            return []
            
        # Get recent messages for this session
        messages = Message.query.filter_by(
            session_id=chat_session.id
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        # Format messages for OpenAI API
        history = []
        for msg in reversed(messages):  # Oldest messages first
            history.append({"role": msg.role, "content": msg.content})
            
        return history
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []

def save_message(session_id, role, content, token_count=None, 
                used_knowledge_base=False, sources=None):
    """Save a message to the database"""
    try:
        # Get or create session
        chat_session = Session.get_or_create(session_id)
        
        # Create new message
        message = Message(
            session_id=chat_session.id,
            role=role,
            content=content,
            token_count=token_count,
            used_knowledge_base=used_knowledge_base,
            sources=json.dumps(sources) if sources else None
        )
        
        # Add and commit
        db.session.add(message)
        db.session.commit()
        
        # Update session's last activity
        chat_session.update_last_activity()
        
        return message
    except Exception as e:
        logger.error(f"Error saving message to database: {str(e)}")
        db.session.rollback()
        return None

@app.route("/chat", methods=["POST"])
def chat():
    """Process chat messages and get AI responses"""
    data = request.json
    user_input = data.get("message", "")
    use_kb = data.get("use_knowledge_base", True)  # Default to using knowledge base
    current_session_id = session.get('session_id')
    
    logger.debug(f"Received message in session {current_session_id}: {user_input}")
    
    if not user_input.strip():
        return jsonify({"reply": "Please enter a message."})
    
    try:
        start_time = time.time()
        
        # Log and count user message tokens
        user_tokens = log_message("user", user_input, DEFAULT_MODEL)
        system_tokens = count_tokens(SYSTEM_PROMPT, DEFAULT_MODEL)
        
        # Save the user message to database
        save_message(current_session_id, "user", user_input, user_tokens)
        
        logger.debug(f"Token counts - System prompt: {system_tokens}, User input: {user_tokens}")
        
        # Get conversation history
        conversation_history = get_conversation_history(current_session_id)
        
        # Try to get information from knowledge base first
        kb_answer = None
        sources = []
        
        if use_kb:
            try:
                logger.info("Querying knowledge base...")
                kb_result = kb_handler.query_knowledge_base(user_input)
                kb_answer = kb_result.get("answer")
                sources = kb_result.get("sources", [])
                logger.info(f"Knowledge base query completed in {time.time() - start_time:.2f}s")
                
                if kb_answer:
                    logger.info("Knowledge base provided an answer")
                else:
                    logger.info("No relevant information found in knowledge base")
            except Exception as kb_error:
                logger.error(f"Error using knowledge base: {str(kb_error)}")
        
        # Prepare messages for OpenAI with conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        # If knowledge base doesn't provide a good answer, use the regular OpenAI completion
        if not kb_answer:
            logger.debug(f"Sending messages to OpenAI: {str(messages)}")
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages
            )
            
            answer = response.choices[0].message.content.strip()
        else:
            answer = kb_answer
        
        # Log and count assistant response tokens
        output_tokens = log_message("assistant", answer, DEFAULT_MODEL)
        total_tokens = system_tokens + user_tokens + output_tokens
        
        # Save the assistant response to database
        save_message(
            current_session_id, 
            "assistant", 
            answer, 
            output_tokens,
            use_kb and kb_answer is not None,
            sources
        )
        
        # Log additional information
        logger.debug(f"Total tokens: {total_tokens}")
        logger.debug(f"Total processing time: {time.time() - start_time:.2f}s")
        logger.info(f"Sources: {sources}")
        
        # Return the response with token information and sources
        response_data = {
            "reply": answer,
            "token_usage": {
                "input_tokens": system_tokens + user_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        }
        
        # Add sources if available
        if sources:
            response_data["sources"] = sources
        
        return jsonify(response_data)
    
    except Exception as e:
        error_msg = f"Error in chat endpoint: {str(e)}"
        logger.error(error_msg)
        log_message("error", error_msg)
        return jsonify({"reply": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Run the server on port 5000 with host 0.0.0.0 (accessible from outside)
    app.run(host="0.0.0.0", port=5000, debug=True)
