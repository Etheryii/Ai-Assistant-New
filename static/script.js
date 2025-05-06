// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const loadingIndicator = document.getElementById('loading-indicator');
    
    // Define the API endpoint - use relative URL for better compatibility
    const API_ENDPOINT = '/chat';
    
    // Scroll to the bottom of the chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add a message to the chat
    function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (!isUser) {
            // Add robot icon for bot messages
            const icon = document.createElement('i');
            icon.className = 'fas fa-robot me-2';
            messageContent.appendChild(icon);
        }
        
        const textSpan = document.createElement('span');
        textSpan.textContent = content;
        messageContent.appendChild(textSpan);
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        // Add robot icon
        const icon = document.createElement('i');
        icon.className = 'fas fa-robot me-2';
        typingDiv.appendChild(icon);
        
        // Add dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingDiv.appendChild(dot);
        }
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Handle sending messages
    async function sendMessage(message) {
        // Add user message to chat
        addMessage(message, true);
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        showTypingIndicator();
        
        try {
            // Send request to API
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            // Hide typing indicator
            hideTypingIndicator();
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response to chat
            addMessage(data.reply, false);
            
            // Check if token usage info is available
            if (data.token_usage) {
                // Log token usage to console
                console.log('Token usage:', data.token_usage);
                
                // Display token usage in a small info message
                const tokenInfo = document.createElement('div');
                tokenInfo.className = 'token-info text-muted small mt-1 mb-3';
                tokenInfo.innerHTML = `
                    <small>
                        <i class="fas fa-info-circle me-1"></i>
                        Token usage: ${data.token_usage.total_tokens} total 
                        (${data.token_usage.input_tokens} input, ${data.token_usage.output_tokens} output)
                    </small>
                `;
                chatMessages.appendChild(tokenInfo);
                scrollToBottom();
            }
        } catch (error) {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Show error message
            addMessage(`Sorry, there was an error: ${error.message}`, false);
            console.error('Error:', error);
        } finally {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
        }
    }
    
    // Form submission handler
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
            userInput.value = '';
        }
    });
    
    // Focus input on page load
    userInput.focus();
    
    // Add event listener for Enter key
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
});
