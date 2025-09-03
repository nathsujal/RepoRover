// Landing Page JavaScript

// Global state
let currentRepo = '';

// Repository form submission
document.getElementById('repo-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const repoUrl = document.getElementById('repo-url').value.trim();
    if (!repoUrl) return;

    const repoName = repoUrl.split('/').slice(-2).join('/');
    currentRepo = repoName;
    
    // Store repository info in sessionStorage for other pages
    sessionStorage.setItem('currentRepo', currentRepo);
    sessionStorage.setItem('repoUrl', repoUrl);
    
    try {
        const response = await fetch('/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ github_url: repoUrl }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start ingestion');
        }

        const data = await response.json();
        const taskId = data.task_id;

        if (taskId) {
            // Store task ID and redirect to processing page
            sessionStorage.setItem('taskId', taskId);
            window.location.href = 'processing.html';
        } else {
            throw new Error("Did not receive a task ID from the server.");
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Clear any existing session data when landing on home page
    sessionStorage.clear();
    
    // Add fade-in animation to main content
    document.body.classList.add('fade-in');
});