// Processing Page JavaScript

// Global state
let pollInterval = null;
let lastLogMessage = '';

// Initialize processing page
document.addEventListener('DOMContentLoaded', () => {
    const taskId = sessionStorage.getItem('taskId');
    const repoUrl = sessionStorage.getItem('repoUrl');
    const currentRepo = sessionStorage.getItem('currentRepo');
    
    if (!taskId || !repoUrl || !currentRepo) {
        // Redirect to home if no task data
        window.location.href = 'index.html';
        return;
    }
    
    // Display current repository
    document.getElementById('current-repo').textContent = repoUrl;
    
    // Start polling for status
    startPolling(taskId);
});

// Polling for ingestion status
function startPolling(taskId) {
    if (pollInterval) clearInterval(pollInterval);

    addLogEntry('Request received, starting ingestion...', 'progress');

    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/ingest/status/${taskId}`);
            if (!response.ok) {
                throw new Error(`Server returned status: ${response.status}`);
            }
            
            const data = await response.json();
            updateLog(data.message, data.status);

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                pollInterval = null;
                setTimeout(() => {
                    window.location.href = 'chat.html';
                }, 1500);
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                pollInterval = null;
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 3000);
            }
        } catch (error) {
            updateLog('Failed to get status: ' + error.message, 'error');
            clearInterval(pollInterval);
            pollInterval = null;
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 3000);
        }
    }, 2500);
}

function updateLog(message, status) {
    if (message === lastLogMessage) return;
    lastLogMessage = message;
    addLogEntry(message, status);
}

function addLogEntry(message, status) {
    const logContainer = document.getElementById('log-container');
    const logEntry = document.createElement('div');
    logEntry.className = 'flex items-center';
    
    let icon, statusText, statusClass;
    
    switch (status) {
        case 'completed':
        case 'success':
            icon = '<div class="w-2.5 h-2.5 bg-green-500 rounded-full"></div>';
            statusText = 'Done';
            statusClass = 'text-green-500';
            break;
        case 'ingesting':
        case 'progress':
            icon = '<svg class="spin h-4 w-4 text-[var(--primary-color)]" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path></svg>';
            statusText = 'In Progress';
            statusClass = 'text-[var(--primary-color)]';
            break;
        case 'error':
            icon = '<div class="w-2.5 h-2.5 bg-red-500 rounded-full"></div>';
            statusText = 'Error';
            statusClass = 'text-red-500';
            break;
        default:
            icon = '<div class="w-2.5 h-2.5 bg-gray-400 rounded-full"></div>';
            statusText = 'Pending';
            statusClass = 'text-gray-500';
    }
    
    logEntry.innerHTML = `
        <div class="w-6 h-6 flex items-center justify-center mr-3">
            ${icon}
        </div>
        <span>${message}</span>
        <span class="ml-auto ${statusClass} font-semibold">${statusText}</span>
    `;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
});