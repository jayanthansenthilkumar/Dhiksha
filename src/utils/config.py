"""
Configuration management using Pydantic Settings.
Loads from environment variables with sensible defaults.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Learning Recommendation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database
    DATABASE_URL: str = "postgresql://admin:localdev@localhost:5432/recommendations"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_SECONDS: int = 3600  # 1 hour
    
    # MinIO / S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_EVENTS: str = "learning-events"
    S3_BUCKET_FEATURES: str = "learning-features"
    S3_BUCKET_MODELS: str = "learning-models"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "user-events"
    
    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "content_embeddings"
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    
    # Model Configuration
    EMBEDDING_DIM: int = 128
    TOP_K_RETRIEVAL: int = 100  # Number of candidates from ANN search
    TOP_K_RANKING: int = 10  # Final number of recommendations
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # BentoML
    BENTOML_HOST: str = "localhost"
    BENTOML_PORT: int = 3000
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    ENABLE_TRACING: bool = True
    
    # Feature flags
    ENABLE_CACHING: bool = True
    ENABLE_AUTH: bool = False  # Set to True in production
    ENABLE_RATE_LIMITING: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL, handling async drivers."""
    return settings.DATABASE_URL


def get_s3_config() -> dict:
    """Get S3 configuration dict."""
    return {
        "endpoint_url": settings.S3_ENDPOINT,
        "aws_access_key_id": settings.S3_ACCESS_KEY,
        "aws_secret_access_key": settings.S3_SECRET_KEY,
    }


def get_redis_config() -> dict:
    """Get Redis configuration dict."""
    from urllib.parse import urlparse
    
    parsed = urlparse(settings.REDIS_URL)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "db": int(parsed.path.lstrip('/')) if parsed.path else 0,
        "decode_responses": True,
    }


def get_milvus_config() -> dict:
    """Get Milvus configuration dict."""
    return {
        "host": settings.MILVUS_HOST,
        "port": settings.MILVUS_PORT,
    }
