from flask import Flask, render_template, request, jsonify
import openai
import os
import logging
import tiktoken
import time
from knowledge_base_handler import KnowledgeBaseHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize knowledge base handler
kb_handler = KnowledgeBaseHandler(openai_api_key=openai_api_key)

# Function to count tokens in a text
def count_tokens(text, model="gpt-4o"):
    """Count the number of tokens in a text string using tiktoken."""
    try:
        encoder = tiktoken.encoding_for_model(model)
        return len(encoder.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        # Use cl100k_base as fallback encoding if specific model encoding not found
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))

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

@app.route("/chat", methods=["POST"])
def chat():
    """Process chat messages and get AI responses"""
    data = request.json
    user_input = data.get("message", "")
    use_kb = data.get("use_knowledge_base", True)  # Default to using knowledge base
    
    logger.debug(f"Received message: {user_input}")
    
    if not user_input.strip():
        return jsonify({"reply": "Please enter a message."})
    
    try:
        start_time = time.time()
        
        # Count input tokens
        system_tokens = count_tokens(SYSTEM_PROMPT)
        user_tokens = count_tokens(user_input)
        logger.debug(f"Token counts - System prompt: {system_tokens}, User input: {user_tokens}")
        
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
        
        # If knowledge base doesn't provide a good answer, use the regular OpenAI completion
        if not kb_answer:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ]
            )
            
            answer = response.choices[0].message.content.strip()
        else:
            answer = kb_answer
        
        # Count output tokens
        output_tokens = count_tokens(answer)
        total_tokens = system_tokens + user_tokens + output_tokens
        
        # Log token usage
        logger.debug(f"Output tokens: {output_tokens}, Total tokens: {total_tokens}")
        logger.debug(f"Total processing time: {time.time() - start_time:.2f}s")
        
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
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"reply": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Run the server on port 5000 with host 0.0.0.0 (accessible from outside)
    app.run(host="0.0.0.0", port=5000, debug=True)
