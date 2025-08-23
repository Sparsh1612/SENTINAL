#!/usr/bin/env python3
"""
Simplified Sentinel Fraud Detection API - No Import Issues
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sentinel Fraud Detection API",
    description="Enterprise-grade credit card fraud detection system with explainable AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sentinel-fraud-detection",
        "version": "1.0.0",
        "message": "Basic API is running - full features coming soon!"
    }

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Welcome to Sentinel Fraud Detection System",
        "version": "1.0.0",
        "status": "Basic API Running",
        "docs": "/docs",
        "health": "/health",
        "note": "This is a simplified version while we resolve import issues"
    }

@app.get("/api/v1/status", tags=["Status"])
async def get_status():
    """Get system status"""
    return {
        "system": "Sentinel Fraud Detection",
        "status": "operational",
        "version": "1.0.0",
        "features": [
            "Basic API endpoints",
            "Health monitoring",
            "CORS enabled",
            "Documentation available"
        ],
        "next_steps": [
            "Fix import dependencies",
            "Enable ML models",
            "Connect to database",
            "Enable real-time processing"
        ]
    }

@app.get("/api/v1/status/", tags=["Status"])
async def get_status_alt():
    """Alternative status endpoint (for frontend compatibility)"""
    return {
        "system": "Sentinel Fraud Detection",
        "status": "operational",
        "version": "1.0.0",
        "features": [
            "Basic API endpoints",
            "Health monitoring",
            "CORS enabled",
            "Documentation available"
        ],
        "next_steps": [
            "Fix import dependencies",
            "Enable ML models",
            "Connect to database",
            "Enable real-time processing"
        ]
    }

if __name__ == "__main__":
    logger.info("Starting simplified Sentinel API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
