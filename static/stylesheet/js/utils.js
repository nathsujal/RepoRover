// Utility Functions - Optional shared utilities

// API Helper Functions
class ApiClient {
    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            throw error;
        }
    }
    
    static async get(url) {
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            throw error;
        }
    }
}

// Session Storage Helpers
class SessionManager {
    static set(key, value) {
        try {
            sessionStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn('Failed to save to sessionStorage:', error);
        }
    }
    
    static get(key) {
        try {
            const value = sessionStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            console.warn('Failed to read from sessionStorage:', error);
            return null;
        }
    }
    
    static remove(key) {
        try {
            sessionStorage.removeItem(key);
        } catch (error) {
            console.warn('Failed to remove from sessionStorage:', error);
        }
    }
    
    static clear() {
        try {
            sessionStorage.clear();
        } catch (error) {
            console.warn('Failed to clear sessionStorage:', error);
        }
    }
}

// URL Validation
class UrlValidator {
    static isValidGitHubUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname === 'github.com' && 
                   urlObj.pathname.split('/').length >= 3 &&
                   urlObj.pathname !== '/';
        } catch (error) {
            return false;
        }
    }
    
    static extractRepoName(url) {
        try {
            const urlObj = new URL(url);
            const pathParts = urlObj.pathname.split('/').filter(part => part);
            if (pathParts.length >= 2) {
                return `${pathParts[0]}/${pathParts[1]}`;
            }
            return null;
        } catch (error) {
            return null;
        }
    }
}

// UI Helpers
class UIHelpers {
    static showToast(message, type = 'info', duration = 3000) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-0`;
        
        // Set colors based on type
        const colors = {
            info: 'bg-blue-500 text-white',
            success: 'bg-green-500 text-white',
            warning: 'bg-yellow-500 text-white',
            error: 'bg-red-500 text-white'
        };
        
        toast.className += ` ${colors[type] || colors.info}`;
        toast.textContent = message;
        
        // Add to DOM
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after duration
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    static showLoader(element, text = 'Loading...') {
        const loader = document.createElement('div');
        loader.className = 'flex items-center justify-center p-4';
        loader.innerHTML = `
            <svg class="spin h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path>
            </svg>
            ${text}
        `;
        
        element.innerHTML = '';
        element.appendChild(loader);
        
        return loader;
    }
    
    static formatTimestamp(date = new Date()) {
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Error Handling
class ErrorHandler {
    static handle(error, context = '') {
        console.error(`Error${context ? ` in ${context}` : ''}:`, error);
        
        let userMessage = 'An unexpected error occurred.';
        
        if (error.message) {
            if (error.message.includes('network') || error.message.includes('fetch')) {
                userMessage = 'Network error. Please check your connection and try again.';
            } else if (error.message.includes('timeout')) {
                userMessage = 'Request timed out. Please try again.';
            } else {
                userMessage = error.message;
            }
        }
        
        UIHelpers.showToast(userMessage, 'error', 5000);
        return userMessage;
    }
}

// Export for use in other scripts (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ApiClient,
        SessionManager,
        UrlValidator,
        UIHelpers,
        ErrorHandler
    };
}