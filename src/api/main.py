"""
FastAPI Gateway - Main Application Entry Point
Orchestrates recommendation requests, event ingestion, and admin endpoints.
"""

import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn

from src.data.schemas import (
    EventCreate,
    EventSchema,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
)
from src.utils.config import settings

# Prometheus metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)
recommendation_latency = Histogram(
    "recommendation_latency_seconds",
    "Recommendation request latency",
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0]
)
model_score_metric = Histogram(
    "model_score",
    "Distribution of model scores",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    # Startup
    print("🚀 Starting Learning Recommendation API...")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug mode: {settings.DEBUG}")
    
    # Initialize connections (e.g., database pool, Redis, etc.)
    # In production, initialize here
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Learning Recommendation API...")
    # Cleanup connections


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Learning Recommendation System API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Record metrics for all requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Recommendation endpoint
@app.get("/recommend/{user_id}", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(
    user_id: str,
    k: int = 10,
):
    """
    Get personalized recommendations for a user.
    
    Args:
        user_id: UUID of the user
        k: Number of recommendations (1-100)
    
    Returns:
        Ordered list of recommended content with scores
    """
    if k < 1 or k > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="k must be between 1 and 100"
        )
    
    start_time = time.time()
    
    try:
        # TODO: Implement recommendation logic
        # 1. Fetch user profile from DB
        # 2. Get cached features from Redis
        # 3. Generate user embedding (or retrieve from cache)
        # 4. Query Milvus for top-K similar items
        # 5. Re-rank with ranking model
        # 6. Return top-N
        
        # Mock response for now
        recommendations = [
            RecommendationItem(
                content_id=f"content_{i}",
                score=0.9 - (i * 0.05),
                reason_tags=["popular", "similar_to_recent"]
            )
            for i in range(k)
        ]
        
        latency_ms = int((time.time() - start_time) * 1000)
        recommendation_latency.observe(time.time() - start_time)
        
        # Log scores for monitoring
        for rec in recommendations:
            model_score_metric.observe(rec.score)
        
        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            model_version="v1.0.0-mock",
            latency_ms=latency_ms
        )
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


# Event ingestion endpoint
@app.post("/events", status_code=status.HTTP_202_ACCEPTED, tags=["Events"])
async def ingest_event(event: EventCreate):
    """
    Ingest a user-content interaction event.
    
    Args:
        event: Event data (user_id, content_id, event_type, value, ts)
    
    Returns:
        Acknowledgment (event is queued for processing)
    """
    try:
        # TODO: Implement event ingestion
        # 1. Validate event
        # 2. Publish to Kafka topic
        # 3. Return 202 Accepted (async processing)
        
        # Mock implementation
        return {
            "status": "accepted",
            "message": "Event queued for processing",
            "event_id": "mock-event-id"
        }
    
    except Exception as e:
        print(f"Error ingesting event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest event"
        )


# Admin endpoints (protected in production with auth)
@app.post("/admin/train", tags=["Admin"])
async def trigger_training(model_name: str = "ranking"):
    """
    Trigger model retraining (admin only).
    
    Args:
        model_name: Name of model to retrain ("retrieval" or "ranking")
    """
    if model_name not in ["retrieval", "ranking"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_name must be 'retrieval' or 'ranking'"
        )
    
    try:
        # TODO: Trigger Prefect flow for training
        return {
            "status": "triggered",
            "model_name": model_name,
            "message": f"Training job for {model_name} model queued"
        }
    
    except Exception as e:
        print(f"Error triggering training: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger training"
        )


@app.post("/admin/reindex", tags=["Admin"])
async def trigger_reindex():
    """
    Trigger Milvus index rebuild (admin only).
    """
    try:
        # TODO: Trigger index rebuild job
        return {
            "status": "triggered",
            "message": "Index rebuild queued"
        }
    
    except Exception as e:
        print(f"Error triggering reindex: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger reindex"
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root with basic info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
