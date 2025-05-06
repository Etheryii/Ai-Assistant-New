from flask import Flask, render_template, request, jsonify
import openai
import os
import logging
import tiktoken

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

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
If you don't know the answer to a question, be honest about it instead of making something up.
"""

@app.route("/")
def home():
    """Render the chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Process chat messages and get AI responses"""
    data = request.json
    user_input = data.get("message", "")
    
    logger.debug(f"Received message: {user_input}")
    
    if not user_input.strip():
        return jsonify({"reply": "Please enter a message."})
    
    try:
        # Count input tokens
        system_tokens = count_tokens(SYSTEM_PROMPT)
        user_tokens = count_tokens(user_input)
        logger.debug(f"Token counts - System prompt: {system_tokens}, User input: {user_tokens}")
        
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
        
        # Count output tokens
        output_tokens = count_tokens(answer)
        total_tokens = system_tokens + user_tokens + output_tokens
        
        # Log token usage
        logger.debug(f"Output tokens: {output_tokens}, Total tokens: {total_tokens}")
        
        # Return the response with token information
        return jsonify({
            "reply": answer,
            "token_usage": {
                "input_tokens": system_tokens + user_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"reply": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Run the server on port 5000 with host 0.0.0.0 (accessible from outside)
    app.run(host="0.0.0.0", port=5000, debug=True)
