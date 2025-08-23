"""
Application configuration for Aegis Fraud Detection System
Author: Sparsh
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Sentinel Fraud Detection"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # Trusted Hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Database
    DATABASE_URL: str = "postgresql://sentinel:password@localhost:5432/sentinel_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_POOL_SIZE: int = 10
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_TRANSACTIONS: str = "transactions"
    KAFKA_TOPIC_ALERTS: str = "fraud_alerts"
    KAFKA_GROUP_ID: str = "sentinel_consumer"
    
    # Machine Learning
    MODEL_PATH: str = "data/models"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    CONFIDENCE_THRESHOLD: float = 0.8
    FRAUD_THRESHOLD: float = 0.7
    
    # Features
    ENABLE_EXPLAINABILITY: bool = True
    ENABLE_FEEDBACK_LOOP: bool = True
    ENABLE_PLUGIN_SYSTEM: bool = True
    ENABLE_REAL_TIME_PROCESSING: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_HEALTH_CHECKS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 1000
    RATE_LIMIT_BURST: int = 100
    
    # File Upload
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "data/uploads"
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000
    
    # Alerting
    ALERT_RETENTION_DAYS: int = 90
    ALERT_BATCH_SIZE: int = 100
    
    # Performance
    BATCH_PROCESSING_SIZE: int = 1000
    MAX_CONCURRENT_REQUESTS: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
elif os.getenv("ENVIRONMENT") == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
