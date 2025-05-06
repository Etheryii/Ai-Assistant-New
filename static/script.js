// Script for AI Support Bot Chat Interface

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const useKnowledgeBaseToggle = document.getElementById('use-knowledge-base');
    
    // Token counter elements
    const inputTokensElement = document.getElementById('input-tokens');
    const outputTokensElement = document.getElementById('output-tokens');
    const totalTokensElement = document.getElementById('total-tokens');
    
    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to server
        sendMessage(message);
    });
    
    // Function to scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add a message to the chat
    function addMessage(content, isUser, sources = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        const icon = document.createElement('i');
        icon.className = isUser ? 'fas fa-user' : 'fas fa-robot';
        avatar.appendChild(icon);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Convert markdown-like formatting (for code blocks and links)
        const formattedContent = formatMessageContent(content);
        messageContent.innerHTML = formattedContent;
        
        // Add sources citation if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'source-citation';
            sourcesDiv.textContent = 'Sources: ' + sources.join(', ');
            messageContent.appendChild(sourcesDiv);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Function to format message content (basic markdown-like formatting)
    function formatMessageContent(content) {
        // Convert URLs to links
        content = content.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert ```code blocks``` to <pre><code> elements
        content = content.replace(
            /```([^`]+)```/g, 
            '<pre><code>$1</code></pre>'
        );
        
        // Convert `inline code` to <code> elements
        content = content.replace(
            /`([^`]+)`/g, 
            '<code>$1</code>'
        );
        
        // Convert line breaks to <p> tags
        const paragraphs = content.split('\n\n');
        return paragraphs.map(p => {
            if (p.trim().length === 0) return '';
            if (p.includes('<pre>')) return p; // Don't wrap code blocks
            return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
        }).join('');
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        typingIndicator.style.display = 'inline-flex';
        scrollToBottom();
    }
    
    // Function to hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }
    
    // Function to send message to server
    async function sendMessage(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    use_knowledge_base: useKnowledgeBaseToggle.checked
                })
            });
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Display bot response
            addMessage(data.reply, false, data.sources);
            
            // Update token usage information
            if (data.token_usage) {
                inputTokensElement.textContent = data.token_usage.input_tokens;
                outputTokensElement.textContent = data.token_usage.output_tokens;
                totalTokensElement.textContent = data.token_usage.total_tokens;
            }
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('Sorry, there was an error processing your request. Please try again.', false);
        }
    }
});