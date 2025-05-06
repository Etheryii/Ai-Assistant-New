// Script for Etherius AI Support Bot Interface

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const useKnowledgeBaseToggle = document.getElementById('use-knowledge-base');
    const chatContainer = document.getElementById('chat-container');
    
    // Initialize - focus on input
    userInput.focus();
    
    // Generate stars dynamically (optional enhancement)
    function generateStars() {
        const starsContainer = document.querySelector('.stars-container');
        if (starsContainer) {
            const starCount = 100;
            for (let i = 0; i < starCount; i++) {
                const star = document.createElement('div');
                star.className = 'star';
                star.style.top = `${Math.random() * 100}%`;
                star.style.left = `${Math.random() * 100}%`;
                star.style.animationDelay = `${Math.random() * 10}s`;
                starsContainer.appendChild(star);
            }
        }
    }
    
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
        userInput.focus();
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to server
        sendMessage(message);
    });
    
    // Function to scroll chat to bottom with smooth animation
    function scrollToBottom() {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
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
        
        // Add a small delay before scrolling to allow the DOM to update
        setTimeout(scrollToBottom, 50);
    }
    
    // Function to format message content (enhanced markdown-like formatting)
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
        
        // Convert ```language code blocks with language specifier
        content = content.replace(
            /```(\w+)\n([^`]+)```/g, 
            '<pre><code class="language-$1">$2</code></pre>'
        );
        
        // Convert `inline code` to <code> elements
        content = content.replace(
            /`([^`]+)`/g, 
            '<code>$1</code>'
        );
        
        // Convert **bold** to <strong> elements
        content = content.replace(
            /\*\*([^*]+)\*\*/g, 
            '<strong>$1</strong>'
        );
        
        // Convert *italic* to <em> elements
        content = content.replace(
            /\*([^*]+)\*/g, 
            '<em>$1</em>'
        );
        
        // Convert line breaks to <p> tags
        const paragraphs = content.split('\n\n');
        return paragraphs.map(p => {
            if (p.trim().length === 0) return '';
            if (p.includes('<pre>')) return p; // Don't wrap code blocks
            return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
        }).join('');
    }
    
    // Function to show typing indicator with glow effect
    function showTypingIndicator() {
        typingIndicator.style.display = 'inline-flex';
        scrollToBottom();
    }
    
    // Function to hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }
    
    // Function to send message to server with improved error handling
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
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('Sorry, there was an error processing your request. Please try again.', false);
        }
    }
    
    // Add keyboard shortcut for sending messages with Enter key (if not using Shift+Enter for newlines)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Initialize any dynamic UI elements
    // generateStars(); // Uncomment if you want to generate stars dynamically
});