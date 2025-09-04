// Chat Interface JavaScript

// Initialize chat page
document.addEventListener('DOMContentLoaded', () => {
    const currentRepo = sessionStorage.getItem('currentRepo');
    
    if (!currentRepo) {
        // Redirect to home if no repo data
        window.location.href = 'index.html';
        return;
    }
    
    // Set repository name in header
    document.getElementById('chat-repo-name').textContent = currentRepo;
    
    // Update welcome message
    document.getElementById('welcome-message').textContent = 
        `Hello! I'm RepoRover. I've finished analyzing the ${currentRepo} repository. How can I help you?`;
    
    // Auto-resize textarea functionality
    setupTextareaResize();
});

// Chat form submission
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;
    
    // Add user message
    addMessage(question, 'user');
    input.value = '';
    resetTextareaHeight();
    
    // Show typing indicator
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
        const answer = result.result?.final_response?.response || result.message || 'Sorry, I could not find an answer.';
        
        // Remove typing indicator and add actual response
        document.getElementById(typingId).remove();
        addMessage(answer, 'agent');
        
    } catch (error) {
        // Remove typing indicator and show error
        document.getElementById(typingId).remove();
        addMessage('Sorry, I encountered an error: ' + error.message, 'agent');
    }
});

function addMessage(text, role, isTyping = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    messageDiv.id = messageId;
    messageDiv.className = `flex items-start gap-4 ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="bg-blue-500 text-white p-4 rounded-lg rounded-br-none shadow-sm max-w-lg">
                <p>${escapeHtml(text)}</p>
            </div>
            <div class="flex-shrink-0 size-10 rounded-full bg-cover bg-center" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuAaK4Zqb5XehE3R3EPa-WFkg5fbj7axcVSKRwZ1HT1-n7JOBrZLKCui65WVatdeunU2KOTpwExrc5CCHs4nurH1-eEu2_pjhhUObtCxsyBCywdCMBQdBO8rBBBl9RoxcwyACeooQoJj-fr98Dq3KonruMuQ4AeSO0mzC3qh-JrdCeFKqbIj1khslMD_1DWIbdmw6uRyAum4rp3Yrq5US9BdII0RSBMO4MphhOk3cuds6ld_DWWSY_bQKZ4b2GxM8O1wPlMLo7g9b3c");'></div>
        `;
    } else {
        const content = isTyping ? 
            '<div class="flex items-center space-x-1"><div class="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div><div class="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style="animation-delay: 0.2s"></div><div class="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style="animation-delay: 0.4s"></div></div>' :
            `<p class="font-bold text-gray-900 mb-1">RepoRover</p><div class="text-gray-700">${formatMessage(text)}</div>`;
        
        messageDiv.innerHTML = `
            <div class="flex-shrink-0 size-10 rounded-full bg-[var(--primary-color)] flex items-center justify-center text-white font-bold text-xl">
                R
            </div>
            <div class="bg-white p-4 rounded-lg rounded-tl-none shadow-sm max-w-lg">
                ${content}
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    return messageId;
}

function setupTextareaResize() {
    const textarea = document.getElementById('chat-input');
    
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
    
    // Handle Enter key for submission (Shift+Enter for new line)
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }
    });
}

function resetTextareaHeight() {
    const textarea = document.getElementById('chat-input');
    textarea.style.height = '3rem'; // Reset to initial height (h-12)
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessage(text) {
    // Basic formatting for better readability
    if (!text) return '';
    
    // Convert line breaks to HTML
    text = escapeHtml(text);
    
    // Convert double line breaks to paragraphs
    text = text.replace(/\n\n/g, '</p><p>');
    
    // Convert single line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags if not already wrapped
    if (!text.startsWith('<p>')) {
        text = '<p>' + text + '</p>';
    }
    
    // Handle markdown-style code blocks (basic support)
    text = text.replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 p-2 rounded mt-2 mb-2 overflow-x-auto"><code>$1</code></pre>');
    
    // Handle inline code
    text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>');
    
    // Handle bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return text;
}