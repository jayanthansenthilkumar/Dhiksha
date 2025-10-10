# Local Setup - Run Without Docker
# Simple SQLite-based setup for quick testing

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import string
import uvicorn

# Simple in-memory mock data
MOCK_USERS = [f"user_{i}" for i in range(1, 101)]
MOCK_CONTENT = [f"content_{i}" for i in range(1, 501)]
MOCK_EVENTS = []

# Pydantic Models
class RecommendationRequest(BaseModel):
    user_id: str
    k: int = 10

class Recommendation(BaseModel):
    content_id: str
    score: float
    reason_tags: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[Recommendation]
    model_version: str
    latency_ms: int

class EventCreate(BaseModel):
    user_id: str
    content_id: str
    event_type: str
    value: Optional[float] = None
    ts: Optional[str] = None

class EventResponse(BaseModel):
    event_id: str
    status: str

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

# Initialize FastAPI
app = FastAPI(
    title="AI Learning Recommender - Local Mode",
    description="Simple local setup without Docker",
    version="1.0.0-local"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
try:
    app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
except Exception as e:
    print(f"Warning: Could not mount frontend directory: {e}")

# Routes
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Learning Recommender API - Local Mode",
        "frontend": "http://localhost:8000/frontend/index.html",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0-local",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/recommend/{user_id}", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(user_id: str, k: int = 10):
    """Get personalized recommendations for a user (mock implementation)"""
    
    # Simulate some latency
    import time
    start = time.time()
    
    # Generate mock recommendations
    recommendations = []
    sample_content = random.sample(MOCK_CONTENT, min(k, len(MOCK_CONTENT)))
    
    for i, content_id in enumerate(sample_content):
        score = 1.0 - (i * 0.05) + random.uniform(-0.1, 0.1)
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        # Random tags
        all_tags = ["python", "machine-learning", "data-science", "web-dev", "algorithms", "cloud"]
        tags = random.sample(all_tags, random.randint(1, 3))
        
        recommendations.append(
            Recommendation(
                content_id=content_id,
                score=score,
                reason_tags=tags
            )
        )
    
    latency = int((time.time() - start) * 1000)
    
    return {
        "user_id": user_id,
        "recommendations": recommendations,
        "model_version": "mock-v1.0.0",
        "latency_ms": latency
    }

@app.post("/events", response_model=EventResponse, tags=["Events"])
async def log_event(event: EventCreate):
    """Log a user event (mock implementation)"""
    
    event_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    
    # Store in memory
    MOCK_EVENTS.append({
        "event_id": event_id,
        "user_id": event.user_id,
        "content_id": event.content_id,
        "event_type": event.event_type,
        "value": event.value,
        "ts": event.ts or datetime.now().isoformat()
    })
    
    print(f"📝 Event logged: {event.event_type} | User: {event.user_id} | Content: {event.content_id}")
    
    return {
        "event_id": event_id,
        "status": "success"
    }

@app.get("/stats", tags=["System"])
async def get_stats():
    """Get system statistics"""
    return {
        "total_users": len(MOCK_USERS),
        "total_content": len(MOCK_CONTENT),
        "total_events": len(MOCK_EVENTS),
        "model_version": "mock-v1.0.0"
    }

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 AI Learning Recommender - Local Mode")
    print("=" * 80)
    print(f"✅ API running at: http://localhost:8000")
    print(f"✅ Frontend at: http://localhost:8000/frontend/index.html")
    print(f"✅ API Docs at: http://localhost:8000/docs")
    print(f"✅ Mock Users: {len(MOCK_USERS)}")
    print(f"✅ Mock Content: {len(MOCK_CONTENT)}")
    print("=" * 80)
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
