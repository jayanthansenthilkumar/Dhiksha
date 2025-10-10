// Configuration
const API_BASE_URL = 'http://localhost:8000';

// Check API status on page load
window.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    loadStats();
});

// Check if API is running
async function checkAPIStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok && data.status === 'healthy') {
            statusDot.className = 'status-indicator online';
            statusText.textContent = `API Online (${data.version})`;
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        statusDot.className = 'status-indicator offline';
        statusText.textContent = 'API Offline - Start server with: uvicorn src.api.main:app --reload';
        console.error('API Status Error:', error);
    }
}

// Get recommendations for a user
async function getRecommendations() {
    const userId = document.getElementById('userId').value.trim();
    const numRecs = document.getElementById('numRecs').value;
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('recommendationsSection').style.display = 'none';
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/recommend/${userId}?k=${numRecs}`);
        const latency = Date.now() - startTime;
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        displayRecommendations(data, latency);
        
    } catch (error) {
        console.error('Recommendation Error:', error);
        alert(`Failed to get recommendations: ${error.message}`);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Display recommendations
function displayRecommendations(data, clientLatency) {
    const section = document.getElementById('recommendationsSection');
    const list = document.getElementById('recommendationsList');
    const metaInfo = document.getElementById('metaInfo');
    
    // Meta info
    metaInfo.innerHTML = `
        <span><strong>User:</strong> ${data.user_id}</span>
        <span><strong>Model:</strong> ${data.model_version}</span>
        <span><strong>Server Latency:</strong> ${data.latency_ms}ms</span>
        <span><strong>Client Latency:</strong> ${clientLatency}ms</span>
    `;
    
    // Recommendations
    list.innerHTML = data.recommendations.map((rec, index) => `
        <div class="recommendation-card">
            <div class="rec-rank">#${index + 1}</div>
            <div class="rec-content">
                <div class="rec-header">
                    <h3 class="rec-title">${getContentTitle(rec.content_id)}</h3>
                    <div class="rec-score">${(rec.score * 100).toFixed(1)}%</div>
                </div>
                <div class="rec-meta">
                    <span class="rec-id">ID: ${rec.content_id}</span>
                    ${rec.reason_tags ? `
                        <div class="rec-tags">
                            ${rec.reason_tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="rec-actions">
                    <button class="btn-small" onclick="quickLog('${data.user_id}', '${rec.content_id}', 'view')">
                        👁️ View
                    </button>
                    <button class="btn-small" onclick="quickLog('${data.user_id}', '${rec.content_id}', 'like')">
                        ❤️ Like
                    </button>
                    <button class="btn-small" onclick="quickLog('${data.user_id}', '${rec.content_id}', 'complete')">
                        ✅ Complete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth' });
}

// Generate content title from ID (mock)
function getContentTitle(contentId) {
    const titles = [
        'Introduction to Machine Learning',
        'Advanced Python Programming',
        'Data Structures & Algorithms',
        'Web Development with React',
        'Docker & Kubernetes Essentials',
        'TensorFlow for Beginners',
        'System Design Interview Prep',
        'Cloud Computing with AWS',
        'JavaScript Mastery Course',
        'SQL Database Fundamentals'
    ];
    
    // Use content ID to deterministically pick a title
    const hash = contentId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return titles[hash % titles.length];
}

// Log an event
async function logEvent() {
    const userId = document.getElementById('eventUserId').value.trim();
    const contentId = document.getElementById('eventContentId').value.trim();
    const eventType = document.getElementById('eventType').value;
    const eventValue = document.getElementById('eventValue').value;
    
    if (!userId || !contentId) {
        alert('Please enter User ID and Content ID');
        return;
    }
    
    const eventData = {
        user_id: userId,
        content_id: contentId,
        event_type: eventType,
        value: eventValue ? parseFloat(eventValue) : null,
        ts: new Date().toISOString()
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        });
        
        const result = await response.json();
        
        const responseDiv = document.getElementById('eventResponse');
        if (response.ok) {
            responseDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ Event logged successfully! 
                    <br><small>Event ID: ${result.event_id || 'N/A'}</small>
                </div>
            `;
        } else {
            throw new Error(result.detail || 'Failed to log event');
        }
        
        // Clear after 3 seconds
        setTimeout(() => {
            responseDiv.innerHTML = '';
        }, 3000);
        
    } catch (error) {
        console.error('Event Logging Error:', error);
        document.getElementById('eventResponse').innerHTML = `
            <div class="alert alert-error">
                ❌ Failed to log event: ${error.message}
            </div>
        `;
    }
}

// Quick log from recommendation cards
async function quickLog(userId, contentId, eventType) {
    document.getElementById('eventUserId').value = userId;
    document.getElementById('eventContentId').value = contentId;
    document.getElementById('eventType').value = eventType;
    
    await logEvent();
    
    // Visual feedback
    event.target.classList.add('clicked');
    setTimeout(() => {
        event.target.classList.remove('clicked');
    }, 500);
}

// Load system statistics (mock for now)
async function loadStats() {
    // In production, these would come from API endpoints
    document.getElementById('totalUsers').textContent = '1,000';
    document.getElementById('totalContent').textContent = '500';
    document.getElementById('totalEvents').textContent = '10,000';
    
    // Could fetch from /health or custom stats endpoint
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        document.getElementById('modelVersion').textContent = data.version || 'v1.0.0';
    } catch (error) {
        console.error('Stats Error:', error);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Enter key to get recommendations
    if (e.key === 'Enter' && document.activeElement.id === 'userId') {
        getRecommendations();
    }
});
