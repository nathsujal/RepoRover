function setupEnhancedTextarea() {
    const textarea = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const charCounter = document.getElementById('char-counter');
    const charCount = document.getElementById('char-count');
    const maxChars = 500;
    
    // Auto-resize function with no scrollbar
    function autoResize() {
        // Reset height to auto to get the correct scrollHeight
        textarea.style.height = 'auto';
        
        // Calculate the new height
        const newHeight = Math.min(textarea.scrollHeight, 128); // max-height: 8rem = 128px
        textarea.style.height = newHeight + 'px';
        
        // Ensure no scrollbar appears
        if (textarea.scrollHeight > 128) {
            textarea.style.overflowY = 'hidden';
        }
    }
    
    // Input event handler
    textarea.addEventListener('input', function() {
        const text = this.value;
        const length = text.length;
        
        // Auto-resize
        autoResize();
        
        // Update send button state
        sendBtn.disabled = text.trim().length === 0;
        
        // Update character counter
        if (charCount) {
            charCount.textContent = length;
            charCounter.classList.toggle('hidden', length < 400);
            
            // Change color when approaching limit
            if (length > maxChars * 0.9) {
                charCounter.classList.add('text-red-500');
            } else if (length > maxChars * 0.8) {
                charCounter.classList.add('text-yellow-500');
            } else {
                charCounter.classList.remove('text-red-500', 'text-yellow-500');
            }
        }
        
        // Prevent exceeding max characters
        if (length > maxChars) {
            this.value = text.substring(0, maxChars);
            return;
        }
    });
    
    // Keyboard shortcuts
    textarea.addEventListener('keydown', function(e) {
        // Enter to send (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                document.getElementById('chat-form').dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to clear
        if (e.key === 'Escape') {
            this.value = '';
            this.style.height = '3rem';
            sendBtn.disabled = true;
            this.blur();
        }
    });
    
    // Paste handler
    textarea.addEventListener('paste', function(e) {
        setTimeout(() => {
            autoResize();
            sendBtn.disabled = this.value.trim().length === 0;
        }, 0);
    });
    
    // Focus/blur handlers for better UX
    textarea.addEventListener('focus', function() {
        this.parentElement.classList.add('ring-2', 'ring-blue-200');
    });
    
    textarea.addEventListener('blur', function() {
        this.parentElement.classList.remove('ring-2', 'ring-blue-200');
    });
    
    // Initial setup
    sendBtn.disabled = true;
    autoResize();
}

// Enhanced form submission
function setupEnhancedChatForm() {
    document.getElementById('chat-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const typingStatus = document.getElementById('typing-status');
        const question = input.value.trim();
        
        if (!question) return;
        
        // Disable input during processing
        input.disabled = true;
        sendBtn.disabled = true;
        
        // Add user message
        addMessage(question, 'user');
        
        // Clear input and reset height
        input.value = '';
        input.style.height = '3rem';
        
        // Show typing indicator
        if (typingStatus) {
            typingStatus.classList.add('show');
        }
        
        const typingId = addMessage('', 'agent', true);
        
        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get response');
            }
            
            const result = await response.json();
            const answer = result.result?.final_response?.response || 
                          result.message || 
                          'Sorry, I could not find an answer.';
            
            // Remove typing indicator and add actual response
            document.getElementById(typingId).remove();
            addMessage(answer, 'agent');
            
        } catch (error) {
            // Remove typing indicator and show error
            document.getElementById(typingId).remove();
            addMessage('Sorry, I encountered an error: ' + error.message, 'agent');
        } finally {
            // Re-enable input
            input.disabled = false;
            sendBtn.disabled = false;
            
            // Hide typing indicator
            if (typingStatus) {
                typingStatus.classList.remove('show');
            }
            
            // Focus back on input
            input.focus();
        }
    });
}

// Initialize enhanced chat functionality
document.addEventListener('DOMContentLoaded', () => {
    setupEnhancedTextarea();
    setupEnhancedChatForm();
    
    // Focus on input when page loads
    document.getElementById('chat-input').focus();
});

// Add this to your existing addMessage function or replace it
function addMessage(text, role, isTyping = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    messageDiv.id = messageId;
    messageDiv.className = `flex items-start gap-4 ${role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="bg-[var(--primary-color)] text-white p-4 rounded-2xl rounded-br-md shadow-sm max-w-lg break-words">
                <p class="whitespace-pre-wrap">${escapeHtml(text)}</p>
            </div>
            <div class="flex-shrink-0 size-10 rounded-full bg-cover bg-center border-2 border-white shadow-sm" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuAaK4Zqb5XehE3R3EPa-WFkg5fbj7axcVSKRwZ1HT1-n7JOBrZLKCui65WVatdeunU2KOTpwExrc5CCHs4nurH1-eEu2_pjhhUObtCxsyBCywdCMBQdBO8rBBBl9RoxcwyACeooQoJj-fr98Dq3KonruMuQ4AeSO0mzC3qh-JrdCeFKqbIj1khslMD_1DWIbdmw6uRyAum4rp3Yrq5US9BdII0RSBMO4MphhOk3cuds6ld_DWWSY_bQKZ4b2GxM8O1wPlMLo7g9b3c");'></div>
        `;
    } else {
        const content = isTyping ? 
            `<div class="flex items-center space-x-1 py-2">
                <div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
                <div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
                <div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
            </div>` :
            `<p class="font-semibold text-gray-900 mb-2">RepoRover</p>
             <div class="text-gray-700 prose prose-sm max-w-none">${formatMessage(text)}</div>`;
        
        messageDiv.innerHTML = `
            <div class="flex-shrink-0 size-10 rounded-full bg-[var(--primary-color)] flex items-center justify-center text-white font-bold text-lg shadow-sm">
                R
            </div>
            <div class="bg-white p-4 rounded-2xl rounded-tl-md shadow-sm max-w-lg border border-gray-100">
                ${content}
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    return messageId;
}

// Add fade-in animation
const style = document.createElement('style');
style.textContent = `
    .animate-fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);