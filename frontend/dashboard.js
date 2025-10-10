// Dashboard JavaScript - Full Featured

const API_BASE_URL = 'http://localhost:8000';
let ws = null;
let charts = {};
let currentUsersPage = 0;
const usersPerPage = 20;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    await checkAPIStatus();
    await loadOverviewData();
    initializeWebSocket();
    initializeCharts();
    
    // Set default dates for analytics
    const today = new Date();
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    document.getElementById('endDate').valueAsDate = today;
    document.getElementById('startDate').valueAsDate = weekAgo;
}

// API Status Check
async function checkAPIStatus() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok) {
            statusDot.style.background = '#10B981';
            statusText.textContent = `Online (v${data.version})`;
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        statusDot.style.background = '#EF4444';
        statusText.textContent = 'Offline';
        console.error('API Status Error:', error);
    }
}

// Tab Navigation
function showTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const tabMap = {
        'overview': 'overviewTab',
        'recommendations': 'recommendationsTab',
        'users': 'usersTab',
        'content': 'contentTab',
        'events': 'eventsTab',
        'analytics': 'analyticsTab'
    };
    
    document.getElementById(tabMap[tabName]).classList.add('active');
    
    // Update page title
    const titleMap = {
        'overview': 'Dashboard Overview',
        'recommendations': 'Recommendation Engine',
        'users': 'User Management',
        'content': 'Content Library',
        'events': 'Live Event Stream',
        'analytics': 'Advanced Analytics'
    };
    
    document.getElementById('pageTitle').textContent = titleMap[tabName];
    
    // Load tab-specific data
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'users':
            loadUsers();
            break;
        case 'content':
            loadContent();
            break;
        case 'events':
            loadRecentEvents();
            break;
        case 'analytics':
            loadAnalytics();
            break;
    }
}

// Overview Data
async function loadOverviewData() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        const data = await response.json();
        
        // Update stats
        document.getElementById('totalUsers').textContent = data.total_users.toLocaleString();
        document.getElementById('totalContent').textContent = data.total_content.toLocaleString();
        document.getElementById('totalEvents').textContent = data.total_events.toLocaleString();
        document.getElementById('activeUsers').textContent = data.active_users_24h.toLocaleString();
        
        // Update popular content
        updatePopularContent(data.popular_content);
        
        // Update event distribution chart
        updateEventDistributionChart(data.event_distribution);
        
        // Load recent activity
        loadRecentActivity();
        
        // Update engagement chart
        updateEngagementChart();
        
    } catch (error) {
        console.error('Failed to load overview data:', error);
    }
}

function updatePopularContent(content) {
    const container = document.getElementById('popularContent');
    
    if (!content || content.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary)">No data available</p>';
        return;
    }
    
    container.innerHTML = content.map((item, index) => `
        <div class="popular-item">
            <div class="popular-item-info">
                <h4>${item.title}</h4>
                <div class="popular-item-meta">
                    <span>${item.content_type}</span> • <span>${item.interaction_count} interactions</span>
                </div>
            </div>
            <div class="popular-item-count">#${index + 1}</div>
        </div>
    `).join('');
}

async function loadRecentActivity() {
    try {
        const response = await fetch(`${API_BASE_URL}/events/recent?limit=10`);
        const data = await response.json();
        
        const container = document.getElementById('recentActivity');
        
        if (!data.events || data.events.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary)">No recent activity</p>';
            return;
        }
        
        container.innerHTML = data.events.map(event => {
            const iconMap = {
                'view': '👁️',
                'complete': '✅',
                'like': '❤️',
                'quiz_score': '📝',
                'bookmark': '🔖',
                'share': '🔗'
            };
            
            const timeAgo = getTimeAgo(new Date(event.timestamp));
            
            return `
                <div class="activity-item">
                    <div class="activity-icon">${iconMap[event.event_type] || '⚡'}</div>
                    <div class="activity-details">
                        <p><strong>${event.user_name}</strong> ${event.event_type} <em>${event.content_title}</em></p>
                        <div class="activity-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load recent activity:', error);
    }
}

// Charts
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'bottom'
            }
        }
    };
    
    // Event Distribution Chart
    const eventCtx = document.getElementById('eventChart');
    if (eventCtx) {
        charts.eventChart = new Chart(eventCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#4F46E5',
                        '#10B981',
                        '#F59E0B',
                        '#EF4444',
                        '#3B82F6',
                        '#8B5CF6'
                    ]
                }]
            },
            options: chartOptions
        });
    }
    
    // Engagement Chart
    const engagementCtx = document.getElementById('engagementChart');
    if (engagementCtx) {
        charts.engagementChart = new Chart(engagementCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Views',
                        data: [],
                        borderColor: '#4F46E5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Completions',
                        data: [],
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx) {
        charts.performanceChart = new Chart(performanceCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Engagement Score',
                    data: [],
                    backgroundColor: 'rgba(79, 70, 229, 0.8)'
                }]
            },
            options: chartOptions
        });
    }
    
    // Cohort Chart
    const cohortCtx = document.getElementById('cohortChart');
    if (cohortCtx) {
        charts.cohortChart = new Chart(cohortCtx, {
            type: 'pie',
            data: {
                labels: ['Beginner', 'Intermediate', 'Advanced'],
                datasets: [{
                    data: [30, 45, 25],
                    backgroundColor: ['#4F46E5', '#10B981', '#F59E0B']
                }]
            },
            options: chartOptions
        });
    }
    
    // Accuracy Chart
    const accuracyCtx = document.getElementById('accuracyChart');
    if (accuracyCtx) {
        charts.accuracyChart = new Chart(accuracyCtx, {
            type: 'radar',
            data: {
                labels: ['Relevance', 'Diversity', 'Novelty', 'Serendipity', 'Coverage'],
                datasets: [{
                    label: 'Current Model',
                    data: [85, 75, 70, 65, 80],
                    backgroundColor: 'rgba(79, 70, 229, 0.2)',
                    borderColor: '#4F46E5',
                    pointBackgroundColor: '#4F46E5'
                }]
            },
            options: chartOptions
        });
    }
}

function updateEventDistributionChart(distribution) {
    if (!charts.eventChart || !distribution) return;
    
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    
    charts.eventChart.data.labels = labels;
    charts.eventChart.data.datasets[0].data = data;
    charts.eventChart.update();
}

function updateEngagementChart() {
    if (!charts.engagementChart) return;
    
    // Generate mock 7-day trend data
    const labels = [];
    const views = [];
    const completions = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        views.push(Math.floor(Math.random() * 100) + 50);
        completions.push(Math.floor(Math.random() * 50) + 20);
    }
    
    charts.engagementChart.data.labels = labels;
    charts.engagementChart.data.datasets[0].data = views;
    charts.engagementChart.data.datasets[1].data = completions;
    charts.engagementChart.update();
}

// Recommendations
async function testRecommendations() {
    const userId = document.getElementById('recUserId').value;
    const strategy = document.getElementById('recStrategy').value;
    const count = document.getElementById('recCount').value;
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    const container = document.getElementById('recommendationResults');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating recommendations...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/recommend/${userId}?k=${count}&strategy=${strategy}`);
        const data = await response.json();
        
        displayRecommendations(data);
        
    } catch (error) {
        container.innerHTML = `<div class="error">Failed to generate recommendations: ${error.message}</div>`;
        console.error('Recommendation error:', error);
    }
}

function displayRecommendations(data) {
    const container = document.getElementById('recommendationResults');
    
    if (!data.recommendations || data.recommendations.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary)">No recommendations found</p>';
        return;
    }
    
    container.innerHTML = `
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-primary); border-radius: 8px;">
            <p><strong>User:</strong> ${data.user_id} | 
               <strong>Strategy:</strong> ${data.strategy} | 
               <strong>Latency:</strong> ${data.latency_ms}ms | 
               <strong>Model:</strong> ${data.model_version}</p>
        </div>
        ${data.recommendations.map((rec, index) => `
            <div class="rec-card">
                <div class="rec-rank">#${index + 1}</div>
                <h3 class="rec-title">${rec.title}</h3>
                <div class="rec-meta">
                    <span class="rec-badge">${rec.content_type}</span>
                    <span class="rec-badge">${rec.difficulty}</span>
                </div>
                <div class="rec-score-bar">
                    <div class="rec-score-fill" style="width: ${rec.score * 100}%"></div>
                </div>
                <div class="rec-score-text">Confidence: ${(rec.score * 100).toFixed(1)}%</div>
                <div class="rec-tags">
                    ${rec.reason_tags.map(tag => `<span class="rec-tag">${tag}</span>`).join('')}
                </div>
            </div>
        `).join('')}
    `;
}

// Users Management
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users?limit=${usersPerPage}&offset=${currentUsersPage * usersPerPage}`);
        const data = await response.json();
        
        const tbody = document.getElementById('usersTable');
        
        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.users.map(user => `
            <tr>
                <td><strong>${user.user_id}</strong></td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="rec-badge">${user.skill_level}</span></td>
                <td>${user.interests ? user.interests.split(',').slice(0, 2).join(', ') : 'N/A'}</td>
                <td><strong>${user.event_count || 0}</strong></td>
                <td>
                    <button class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem" onclick="viewUserAnalytics('${user.user_id}')">
                        View Analytics
                    </button>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('userPageInfo').textContent = `Page ${currentUsersPage + 1}`;
        
    } catch (error) {
        console.error('Failed to load users:', error);
    }
}

function nextUsersPage() {
    currentUsersPage++;
    loadUsers();
}

function prevUsersPage() {
    if (currentUsersPage > 0) {
        currentUsersPage--;
        loadUsers();
    }
}

function filterUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#usersTable tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

async function viewUserAnalytics(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/user/${userId}`);
        const data = await response.json();
        
        alert(`User Analytics for ${userId}:\n\n` +
              `Total Events: ${data.total_events}\n` +
              `Content Viewed: ${data.content_viewed}\n` +
              `Content Completed: ${data.content_completed}\n` +
              `Avg Quiz Score: ${data.avg_quiz_score.toFixed(1)}\n` +
              `Preferred Topics: ${data.preferred_topics.join(', ')}`);
        
    } catch (error) {
        alert('Failed to load user analytics');
        console.error(error);
    }
}

// Content Management
async function loadContent() {
    try {
        const filter = document.getElementById('contentFilter')?.value || '';
        const search = document.getElementById('contentSearch')?.value || '';
        
        let url = `${API_BASE_URL}/content?limit=100`;
        if (filter) url += `&content_type=${filter}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const container = document.getElementById('contentGrid');
        
        if (!data.content || data.content.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary)">No content found</p>';
            return;
        }
        
        let filteredContent = data.content;
        if (search) {
            filteredContent = filteredContent.filter(item => 
                item.title.toLowerCase().includes(search.toLowerCase()) ||
                item.description.toLowerCase().includes(search.toLowerCase())
            );
        }
        
        container.innerHTML = filteredContent.map(item => {
            const iconMap = {
                'video': '🎥',
                'article': '📄',
                'course': '📚',
                'tutorial': '📖',
                'quiz': '📝',
                'project': '🛠️'
            };
            
            return `
                <div class="content-item-card">
                    <div class="content-thumbnail">${iconMap[item.content_type] || '📄'}</div>
                    <div class="content-item-body">
                        <h3 class="content-item-title">${item.title}</h3>
                        <div class="content-item-meta">
                            <span class="rec-badge">${item.content_type}</span>
                            <span class="rec-badge">${item.difficulty}</span>
                            <span class="rec-badge">${item.duration_minutes}min</span>
                        </div>
                        <p style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.75rem">
                            ${item.description.substring(0, 100)}...
                        </p>
                        <div class="content-item-stats">
                            <span>Popularity: ${(item.popularity_score * 100).toFixed(0)}%</span>
                            <span>${item.content_id}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load content:', error);
    }
}

function filterContent() {
    loadContent();
}

// Live Events
async function loadRecentEvents() {
    try {
        const response = await fetch(`${API_BASE_URL}/events/recent?limit=50`);
        const data = await response.json();
        
        const container = document.getElementById('eventStream');
        
        if (!data.events || data.events.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary)">No events yet</p>';
            return;
        }
        
        container.innerHTML = data.events.map(event => {
            const timeAgo = getTimeAgo(new Date(event.timestamp));
            
            return `
                <div class="event-item">
                    <div style="flex: 1">
                        <p><strong>${event.user_name}</strong> <span style="color: var(--primary)">${event.event_type}</span> 
                           <em>${event.content_title}</em></p>
                        <small style="color: var(--text-secondary)">${timeAgo} • ${event.event_id}</small>
                        ${event.value ? `<div style="margin-top: 0.25rem"><span class="rec-badge">Score: ${event.value}</span></div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load events:', error);
    }
}

// Analytics
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        const data = await response.json();
        
        // Update performance chart
        if (charts.performanceChart && data.popular_content) {
            const labels = data.popular_content.slice(0, 5).map(c => c.title.substring(0, 20) + '...');
            const chartData = data.popular_content.slice(0, 5).map(c => c.interaction_count);
            
            charts.performanceChart.data.labels = labels;
            charts.performanceChart.data.datasets[0].data = chartData;
            charts.performanceChart.update();
        }
        
        // Generate AI insights
        generateAIInsights(data);
        
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function generateAIInsights(data) {
    const container = document.getElementById('aiInsights');
    
    const insights = [
        {
            title: '📈 Engagement Trend',
            text: `Active users in the last 24 hours: ${data.active_users_24h}. This represents ${((data.active_users_24h / data.total_users) * 100).toFixed(1)}% of total users.`
        },
        {
            title: '🎯 Content Performance',
            text: `Top performing content has ${data.popular_content[0]?.interaction_count || 0} interactions. Consider promoting similar content.`
        },
        {
            title: '⚡ Event Distribution',
            text: `Most common event type: ${Object.keys(data.event_distribution).reduce((a, b) => 
                data.event_distribution[a] > data.event_distribution[b] ? a : b)}. Total events: ${data.total_events}.`
        },
        {
            title: '✅ Completion Rate',
            text: `Overall engagement rate is ${(data.engagement_rate * 100).toFixed(1)}%. ${
                data.engagement_rate > 0.5 ? 'Great job!' : 'Consider improving content quality and recommendations.'
            }`
        }
    ];
    
    container.innerHTML = insights.map(insight => `
        <div class="insight-item">
            <h4>${insight.title}</h4>
            <p>${insight.text}</p>
        </div>
    `).join('');
}

function applyDateFilter() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    console.log('Applying date filter:', startDate, 'to', endDate);
    loadAnalytics();
}

// WebSocket for real-time updates
function initializeWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            setTimeout(initializeWebSocket, 5000);
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'event') {
        // Add new event to stream if on events tab
        const eventStream = document.getElementById('eventStream');
        if (eventStream && document.getElementById('eventsTab').classList.contains('active')) {
            const newEvent = document.createElement('div');
            newEvent.className = 'event-item new';
            newEvent.innerHTML = `
                <div style="flex: 1">
                    <p><strong>${data.user_id}</strong> <span style="color: var(--primary)">${data.event_type}</span> 
                       <em>${data.content_id}</em></p>
                    <small style="color: var(--text-secondary)">Just now</small>
                </div>
            `;
            eventStream.insertBefore(newEvent, eventStream.firstChild);
        }
        
        // Refresh overview data
        if (document.getElementById('overviewTab').classList.contains('active')) {
            setTimeout(loadOverviewData, 1000);
        }
    }
}

// Utility Functions
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update theme toggle button
    const btn = document.querySelector('.theme-toggle');
    btn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
if (savedTheme === 'dark') {
    document.querySelector('.theme-toggle').textContent = '☀️';
}

// Global search
document.getElementById('globalSearch')?.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    console.log('Global search:', searchTerm);
    // Implement global search functionality
});

// Auto-refresh overview data every 30 seconds
setInterval(() => {
    if (document.getElementById('overviewTab')?.classList.contains('active')) {
        loadOverviewData();
    }
}, 30000);

console.log('Dashboard initialized successfully');
