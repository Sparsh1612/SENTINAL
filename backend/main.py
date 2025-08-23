from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List

from .api import detection, explanation, feedback, ingestion, plugins
from .core.fraud_detector import FraudDetector
from .core.plugin_system import PluginSystem
from .database import get_db, init_db
from .utils.logger import setup_logger
from .utils.metrics import setup_metrics
from .config import settings

# Setup logging
logger = setup_logger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Sentinel Fraud Detection System...")
    
    # Initialize database
    await init_db()
    
    # Initialize fraud detector
    app.state.fraud_detector = FraudDetector()
    
    # Initialize plugin system
    app.state.plugin_system = PluginSystem()
    
    # Setup metrics
    setup_metrics()
    
    logger.info("Sentinel system started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sentinel system...")

# Create FastAPI app
app = FastAPI(
    title="Sentinel Fraud Detection API",
    description="Enterprise-grade credit card fraud detection system with explainable AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sentinel-fraud-detection",
        "version": "1.0.0"
    }

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Welcome to Sentinel Fraud Detection System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(
    detection.router,
    prefix="/api/v1/detection",
    tags=["Fraud Detection"]
)

app.include_router(
    explanation.router,
    prefix="/api/v1/explanation",
    tags=["Explainable AI"]
)

app.include_router(
    feedback.router,
    prefix="/api/v1/feedback",
    tags=["Feedback System"]
)

app.include_router(
    ingestion.router,
    prefix="/api/v1/ingestion",
    tags=["Data Ingestion"]
)

app.include_router(
    plugins.router,
    prefix="/api/v1/plugins",
    tags=["Plugin System"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
