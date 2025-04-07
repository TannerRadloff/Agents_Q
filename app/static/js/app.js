// Main JavaScript for Agents_Q application

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const modelSelector = document.getElementById('model-selector');
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status span');

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage('user', message);
        
        // Clear input
        userInput.value = '';
        
        // Set status to thinking
        setStatus('thinking', 'Agent is processing...');
        
        // Send message to backend
        sendMessage(message);
    });

    // Function to add a message to the chat
    function addMessage(sender, content, toolsUsed = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        
        // If tools were used, add them to the message
        if (toolsUsed && toolsUsed.length > 0) {
            const toolsDiv = document.createElement('div');
            toolsDiv.className = 'tools-used';
            toolsDiv.textContent = `Tools used: ${toolsUsed.join(', ')}`;
            messageDiv.appendChild(toolsDiv);
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to send message to backend
    function sendMessage(message) {
        const selectedModel = modelSelector.value;

        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message, 
                model: selectedModel 
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Add agent response to chat
            addMessage('agent', data.response, data.tools_used);
            
            // Reset status
            setStatus('ready', 'Ready');
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Add error message to chat
            addMessage('system', 'Sorry, there was an error processing your request. Please try again.');
            
            // Set status to error
            setStatus('error', 'Error occurred');
        });
    }

    // Function to set status
    function setStatus(state, text) {
        statusIndicator.className = 'status-indicator';
        if (state !== 'ready') {
            statusIndicator.classList.add(state);
        }
        statusText.textContent = text;
    }
});
