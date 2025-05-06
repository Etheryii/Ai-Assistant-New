"""
Token counting and logging utilities for the AI Support Bot.
This module provides functions to count tokens in text using tiktoken
and log message information with token counts.
"""

import tiktoken
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
LOG_FILE = "token_logs.txt"  # This will appear in your Replit files
DEFAULT_MODEL = "gpt-4o"  # Using GPT-4o as default model


def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    """Count the number of tokens in a text string using tiktoken.
    
    Args:
        text: The text to count tokens for
        model: The model to use for tokenization (defaults to GPT-4o)
        
    Returns:
        The number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Use cl100k_base as fallback encoding if specific model encoding not found
        logger.warning(f"Encoding for model {model} not found, using cl100k_base instead")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    if not text:
        return 0
        
    tokens = encoding.encode(text)
    return len(tokens)


def log_message(role: str, text: str, model: str = DEFAULT_MODEL) -> int:
    """Log a message with its token count and timestamp.
    
    Args:
        role: The role of the message sender (e.g., "user", "assistant")
        text: The text of the message
        model: The model to use for tokenization (defaults to GPT-4o)
        
    Returns:
        The number of tokens in the message
    """
    token_count = count_tokens(text, model)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] {role.upper()} | Tokens: {token_count} | Message: {text[:100]}{'...' if len(text) > 100 else ''}"
    
    # Log to console
    logger.info(log_entry)
    
    # Log to file
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        logger.error(f"Error writing to log file: {str(e)}")
    
    return token_count