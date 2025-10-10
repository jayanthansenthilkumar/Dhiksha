"""
AI Learning Recommender - Full Featured Implementation
Includes: SQLite DB, Real ML simulation, Analytics, Admin controls, WebSocket support
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import random
import string
import json
import asyncio
import uvicorn
from collections import defaultdict
import math

# Database setup
DB_PATH = "recommender.db"

def init_database():
    """Initialize SQLite database with all tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            cohort_tag TEXT,
            skill_level TEXT,
            interests TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP
        )
    """)
    
    # Content table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            content_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT,
            difficulty TEXT,
            tags TEXT,
            duration_minutes INTEGER,
            popularity_score REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT,
            content_id TEXT,
            event_type TEXT,
            value REAL,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (content_id) REFERENCES content(content_id)
        )
    """)
    
    # Recommendations log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_logs (
            log_id TEXT PRIMARY KEY,
            user_id TEXT,
            content_id TEXT,
            score REAL,
            model_version TEXT,
            reason_tags TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clicked BOOLEAN DEFAULT 0
        )
    """)
    
    # User preferences (learned)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT,
            preference_key TEXT,
            preference_value TEXT,
            confidence REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, preference_key)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_content ON events(content_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recs_user ON recommendation_logs(user_id)")
    
    conn.commit()
    conn.close()

def seed_database():
    """Seed database with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Sample users
    cohorts = ["beginner", "intermediate", "advanced"]
    interests_pool = ["python", "javascript", "machine-learning", "web-dev", "data-science", "cloud", "devops", "ai"]
    
    users = []
    for i in range(1, 101):
        users.append((
            f"user_{i}",
            f"User {i}",
            f"user{i}@example.com",
            random.choice(cohorts),
            random.choice(["novice", "intermediate", "expert"]),
            ",".join(random.sample(interests_pool, random.randint(2, 4))),
            datetime.now() - timedelta(days=random.randint(1, 365))
        ))
    
    cursor.executemany("""
        INSERT INTO users (user_id, name, email, cohort_tag, skill_level, interests, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, users)
    
    # Sample content
    content_types = ["video", "article", "course", "tutorial", "quiz", "project"]
    difficulties = ["beginner", "intermediate", "advanced"]
    
    content_titles = [
        "Introduction to Python Programming",
        "Advanced JavaScript Patterns",
        "Machine Learning Fundamentals",
        "React for Beginners",
        "Docker and Kubernetes",
        "Data Structures and Algorithms",
        "Web Development Bootcamp",
        "TensorFlow Deep Learning",
        "System Design Interview Prep",
        "Cloud Computing with AWS",
        "Python Data Science",
        "Node.js Backend Development",
        "Vue.js Complete Guide",
        "DevOps Best Practices",
        "Natural Language Processing",
        "Computer Vision with OpenCV",
        "SQL Database Mastery",
        "MongoDB NoSQL Basics",
        "REST API Design",
        "GraphQL Fundamentals"
    ]
    
    content = []
    for i in range(1, 201):
        title = random.choice(content_titles) if i > 20 else content_titles[i-1] if i <= len(content_titles) else f"Course {i}"
        content.append((
            f"content_{i}",
            title,
            f"Comprehensive guide to {title.lower()}",
            random.choice(content_types),
            random.choice(difficulties),
            ",".join(random.sample(interests_pool, random.randint(1, 3))),
            random.randint(10, 240),
            random.uniform(0.0, 1.0)
        ))
    
    cursor.executemany("""
        INSERT INTO content (content_id, title, description, content_type, difficulty, tags, duration_minutes, popularity_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, content)
    
    # Sample events
    event_types = ["view", "complete", "like", "quiz_score", "bookmark", "share"]
    events = []
    
    for i in range(1, 5001):
        user_id = f"user_{random.randint(1, 100)}"
        content_id = f"content_{random.randint(1, 200)}"
        event_type = random.choice(event_types)
        value = random.randint(60, 100) if event_type == "quiz_score" else None
        
        events.append((
            f"event_{i}",
            user_id,
            content_id,
            event_type,
            value,
            f"session_{random.randint(1, 1000)}",
            datetime.now() - timedelta(hours=random.randint(1, 720))
        ))
    
    cursor.executemany("""
        INSERT INTO events (event_id, user_id, content_id, event_type, value, session_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, events)
    
    conn.commit()
    conn.close()
    print("✅ Database seeded with sample data")

# Initialize DB on startup
init_database()
seed_database()

# Pydantic Models
class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    cohort_tag: str
    skill_level: str
    interests: List[str]
    created_at: str
    last_active: Optional[str] = None

class ContentItem(BaseModel):
    content_id: str
    title: str
    description: str
    content_type: str
    difficulty: str
    tags: List[str]
    duration_minutes: int
    popularity_score: float

class Recommendation(BaseModel):
    content_id: str
    title: str
    score: float
    reason_tags: List[str]
    difficulty: str
    content_type: str

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[Recommendation]
    model_version: str
    latency_ms: int
    strategy: str

class EventCreate(BaseModel):
    user_id: str
    content_id: str
    event_type: str
    value: Optional[float] = None
    session_id: Optional[str] = None

class EventResponse(BaseModel):
    event_id: str
    status: str
    timestamp: str

class AnalyticsResponse(BaseModel):
    total_users: int
    total_content: int
    total_events: int
    active_users_24h: int
    popular_content: List[Dict[str, Any]]
    event_distribution: Dict[str, int]
    engagement_rate: float

class UserAnalytics(BaseModel):
    user_id: str
    total_events: int
    content_viewed: int
    content_completed: int
    avg_quiz_score: float
    preferred_topics: List[str]
    activity_trend: List[Dict[str, Any]]

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Initialize FastAPI
app = FastAPI(
    title="AI Learning Recommender - Full Featured",
    description="Production-ready recommendation system with analytics",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    pass

# Helper functions
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_user_similarity(user_id: str, target_user_id: str) -> float:
    """Calculate similarity between users based on interaction history"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get common content
    cursor.execute("""
        SELECT COUNT(DISTINCT e1.content_id) as common_content
        FROM events e1
        JOIN events e2 ON e1.content_id = e2.content_id
        WHERE e1.user_id = ? AND e2.user_id = ?
    """, (user_id, target_user_id))
    
    common = cursor.fetchone()['common_content']
    conn.close()
    
    return min(common / 10.0, 1.0)  # Normalize

def get_content_embeddings(content_id: str) -> List[float]:
    """Simulate content embeddings (in production, use real embeddings)"""
    random.seed(hash(content_id))
    return [random.gauss(0, 1) for _ in range(32)]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

# API Routes

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Learning Recommender API - Full Featured",
        "version": "2.0.0",
        "endpoints": {
            "dashboard": "/static/dashboard.html",
            "api_docs": "/docs",
            "health": "/health",
            "analytics": "/analytics",
            "websocket": "/ws"
        }
    }

@app.get("/health", tags=["System"])
async def health():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM content")
    content_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM events")
    event_count = cursor.fetchone()['count']
    
    conn.close()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "users": user_count,
            "content": content_count,
            "events": event_count
        }
    }

@app.get("/recommend/{user_id}", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(
    user_id: str,
    k: int = Query(10, ge=1, le=50),
    strategy: str = Query("hybrid", regex="^(collaborative|content_based|hybrid)$")
):
    """Get personalized recommendations using ML simulation"""
    import time
    start = time.time()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user profile
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_interests = user['interests'].split(',') if user['interests'] else []
    user_skill = user['skill_level']
    
    # Get user's interaction history
    cursor.execute("""
        SELECT content_id, event_type, COUNT(*) as interaction_count
        FROM events
        WHERE user_id = ?
        GROUP BY content_id, event_type
    """, (user_id,))
    
    user_history = defaultdict(dict)
    for row in cursor.fetchall():
        user_history[row['content_id']][row['event_type']] = row['interaction_count']
    
    # Get all content
    cursor.execute("SELECT * FROM content")
    all_content = cursor.fetchall()
    
    # Score each content item
    recommendations = []
    
    for content in all_content:
        content_id = content['content_id']
        
        # Skip already consumed content
        if content_id in user_history and 'complete' in user_history[content_id]:
            continue
        
        score = 0.0
        reason_tags = []
        
        # Content-based scoring
        content_tags = content['tags'].split(',') if content['tags'] else []
        tag_overlap = len(set(user_interests) & set(content_tags))
        
        if tag_overlap > 0:
            score += tag_overlap * 0.3
            reason_tags.extend(list(set(user_interests) & set(content_tags))[:2])
        
        # Difficulty matching
        difficulty_match = {
            "novice": {"beginner": 1.0, "intermediate": 0.5, "advanced": 0.2},
            "intermediate": {"beginner": 0.5, "intermediate": 1.0, "advanced": 0.7},
            "expert": {"beginner": 0.3, "intermediate": 0.7, "advanced": 1.0}
        }
        
        score += difficulty_match.get(user_skill, {}).get(content['difficulty'], 0.5) * 0.2
        
        # Popularity boost
        score += content['popularity_score'] * 0.15
        
        # Collaborative filtering (simplified)
        if strategy in ["collaborative", "hybrid"]:
            # Find similar users
            cursor.execute("""
                SELECT e2.user_id, COUNT(*) as common_items
                FROM events e1
                JOIN events e2 ON e1.content_id = e2.content_id
                WHERE e1.user_id = ? AND e2.user_id != ?
                GROUP BY e2.user_id
                ORDER BY common_items DESC
                LIMIT 10
            """, (user_id, user_id))
            
            similar_users = cursor.fetchall()
            
            # Check if similar users liked this content
            for similar_user in similar_users:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM events
                    WHERE user_id = ? AND content_id = ? AND event_type IN ('like', 'complete')
                """, (similar_user['user_id'], content_id))
                
                if cursor.fetchone()['count'] > 0:
                    score += 0.2
                    reason_tags.append("popular_with_similar_users")
                    break
        
        # Recency penalty for old content
        days_old = (datetime.now() - datetime.fromisoformat(content['created_at'])).days
        recency_factor = max(0.5, 1.0 - (days_old / 365))
        score *= recency_factor
        
        # Add randomness for exploration
        score += random.uniform(0, 0.1)
        
        if not reason_tags:
            reason_tags = ["recommended_for_you"]
        
        recommendations.append({
            "content_id": content_id,
            "title": content['title'],
            "score": min(score, 1.0),
            "reason_tags": reason_tags[:3],
            "difficulty": content['difficulty'],
            "content_type": content['content_type']
        })
    
    # Sort by score and take top k
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_recs = recommendations[:k]
    
    # Log recommendations
    for rec in top_recs:
        log_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        cursor.execute("""
            INSERT INTO recommendation_logs (log_id, user_id, content_id, score, model_version, reason_tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, user_id, rec['content_id'], rec['score'], "v2.0.0", ",".join(rec['reason_tags'])))
    
    conn.commit()
    conn.close()
    
    latency = int((time.time() - start) * 1000)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "recommendation",
        "user_id": user_id,
        "count": len(top_recs),
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "user_id": user_id,
        "recommendations": top_recs,
        "model_version": "v2.0.0",
        "latency_ms": latency,
        "strategy": strategy
    }

@app.post("/events", response_model=EventResponse, tags=["Events"])
async def log_event(event: EventCreate):
    """Log a user event"""
    event_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    timestamp = datetime.now()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify user and content exist
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (event.user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute("SELECT content_id FROM content WHERE content_id = ?", (event.content_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Insert event
    cursor.execute("""
        INSERT INTO events (event_id, user_id, content_id, event_type, value, session_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (event_id, event.user_id, event.content_id, event.event_type, event.value, event.session_id, timestamp))
    
    # Update user last_active
    cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (timestamp, event.user_id))
    
    # Update content popularity
    cursor.execute("""
        UPDATE content
        SET popularity_score = (
            SELECT COUNT(*) * 0.01
            FROM events
            WHERE content_id = ?
        )
        WHERE content_id = ?
    """, (event.content_id, event.content_id))
    
    conn.commit()
    conn.close()
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "event",
        "event_type": event.event_type,
        "user_id": event.user_id,
        "content_id": event.content_id,
        "timestamp": timestamp.isoformat()
    })
    
    return {
        "event_id": event_id,
        "status": "success",
        "timestamp": timestamp.isoformat()
    }

@app.get("/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics():
    """Get system-wide analytics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total counts
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM content")
    total_content = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM events")
    total_events = cursor.fetchone()['count']
    
    # Active users in last 24h
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as count
        FROM events
        WHERE timestamp > datetime('now', '-1 day')
    """)
    active_users_24h = cursor.fetchone()['count']
    
    # Popular content
    cursor.execute("""
        SELECT c.content_id, c.title, c.content_type, COUNT(*) as interaction_count
        FROM events e
        JOIN content c ON e.content_id = c.content_id
        WHERE e.timestamp > datetime('now', '-7 days')
        GROUP BY c.content_id
        ORDER BY interaction_count DESC
        LIMIT 10
    """)
    
    popular_content = [dict(row) for row in cursor.fetchall()]
    
    # Event distribution
    cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM events
        GROUP BY event_type
    """)
    
    event_distribution = {row['event_type']: row['count'] for row in cursor.fetchall()}
    
    # Engagement rate
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT CASE WHEN event_type = 'complete' THEN user_id END) * 1.0 / 
            COUNT(DISTINCT user_id) as engagement_rate
        FROM events
    """)
    
    engagement_rate = cursor.fetchone()['engagement_rate'] or 0.0
    
    conn.close()
    
    return {
        "total_users": total_users,
        "total_content": total_content,
        "total_events": total_events,
        "active_users_24h": active_users_24h,
        "popular_content": popular_content,
        "event_distribution": event_distribution,
        "engagement_rate": engagement_rate
    }

@app.get("/analytics/user/{user_id}", response_model=UserAnalytics, tags=["Analytics"])
async def get_user_analytics(user_id: str):
    """Get analytics for a specific user"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify user exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Total events
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE user_id = ?", (user_id,))
    total_events = cursor.fetchone()['count']
    
    # Content viewed
    cursor.execute("""
        SELECT COUNT(DISTINCT content_id) as count
        FROM events
        WHERE user_id = ? AND event_type = 'view'
    """, (user_id,))
    content_viewed = cursor.fetchone()['count']
    
    # Content completed
    cursor.execute("""
        SELECT COUNT(DISTINCT content_id) as count
        FROM events
        WHERE user_id = ? AND event_type = 'complete'
    """, (user_id,))
    content_completed = cursor.fetchone()['count']
    
    # Average quiz score
    cursor.execute("""
        SELECT AVG(value) as avg_score
        FROM events
        WHERE user_id = ? AND event_type = 'quiz_score'
    """, (user_id,))
    avg_quiz_score = cursor.fetchone()['avg_score'] or 0.0
    
    # Preferred topics
    cursor.execute("""
        SELECT c.tags, COUNT(*) as count
        FROM events e
        JOIN content c ON e.content_id = c.content_id
        WHERE e.user_id = ?
        GROUP BY c.tags
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,))
    
    tag_counts = defaultdict(int)
    for row in cursor.fetchall():
        if row['tags']:
            for tag in row['tags'].split(','):
                tag_counts[tag] += row['count']
    
    preferred_topics = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    preferred_topics = [topic for topic, _ in preferred_topics]
    
    # Activity trend (last 7 days)
    cursor.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM events
        WHERE user_id = ? AND timestamp > datetime('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    """, (user_id,))
    
    activity_trend = [{"date": row['date'], "count": row['count']} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "user_id": user_id,
        "total_events": total_events,
        "content_viewed": content_viewed,
        "content_completed": content_completed,
        "avg_quiz_score": avg_quiz_score,
        "preferred_topics": preferred_topics,
        "activity_trend": activity_trend
    }

@app.get("/users", tags=["Users"])
async def get_users(limit: int = 100, offset: int = 0):
    """Get list of users"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.*, COUNT(e.event_id) as event_count
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        GROUP BY u.user_id
        ORDER BY event_count DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"users": users, "count": len(users)}

@app.get("/content", tags=["Content"])
async def get_content(
    limit: int = 100,
    offset: int = 0,
    difficulty: Optional[str] = None,
    content_type: Optional[str] = None
):
    """Get list of content items"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM content WHERE 1=1"
    params = []
    
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    
    if content_type:
        query += " AND content_type = ?"
        params.append(content_type)
    
    query += " ORDER BY popularity_score DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    content = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"content": content, "count": len(content)}

@app.get("/events/recent", tags=["Events"])
async def get_recent_events(limit: int = 100):
    """Get recent events"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, u.name as user_name, c.title as content_title
        FROM events e
        JOIN users u ON e.user_id = u.user_id
        JOIN content c ON e.content_id = c.content_id
        ORDER BY e.timestamp DESC
        LIMIT ?
    """, (limit,))
    
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"events": events, "count": len(events)}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or process commands
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 AI Learning Recommender - Full Featured Edition")
    print("=" * 80)
    print(f"✅ Dashboard: http://localhost:8000/static/dashboard.html")
    print(f"✅ API Docs: http://localhost:8000/docs")
    print(f"✅ WebSocket: ws://localhost:8000/ws")
    print(f"✅ Database: {DB_PATH}")
    print("=" * 80)
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
