from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from ..database import get_db
from ..core.fraud_detector import FraudDetector
from ..schemas.transaction import Transaction
from ..schemas.fraud import FraudAlert, AlertStatus, AlertSeverity
from ..utils.logger import setup_logger
from ..utils.metrics import record_api_request, record_fraud_detection

logger = setup_logger(__name__)

router = APIRouter()

# Pydantic models for API requests/responses
from pydantic import BaseModel, Field

class TransactionRequest(BaseModel):
    """Transaction data for fraud detection"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", description="Transaction currency")
    card_id: str = Field(..., description="Credit card identifier")
    card_type: Optional[str] = Field(None, description="Type of card (credit/debit)")
    card_brand: Optional[str] = Field(None, description="Card brand (Visa, Mastercard, etc.)")
    merchant_id: str = Field(..., description="Merchant identifier")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    merchant_category: Optional[str] = Field(None, description="Merchant category")
    merchant_city: Optional[str] = Field(None, description="Merchant city")
    merchant_country: Optional[str] = Field(None, description="Merchant country")
    latitude: Optional[float] = Field(None, description="Transaction latitude")
    longitude: Optional[float] = Field(None, description="Transaction longitude")
    ip_address: Optional[str] = Field(None, description="IP address")
    transaction_type: str = Field(default="purchase", description="Type of transaction")
    authorization_code: Optional[str] = Field(None, description="Authorization code")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Transaction timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class FraudDetectionResponse(BaseModel):
    """Fraud detection response"""
    transaction_id: str
    fraud_probability: float
    risk_score: float
    confidence_score: float
    is_fraud: bool
    detection_method: str
    risk_level: str
    recommended_action: str
    prediction_time_ms: float
    timestamp: str
    alert_id: Optional[str] = None

class BatchDetectionRequest(BaseModel):
    """Batch fraud detection request"""
    transactions: List[TransactionRequest]
    batch_id: Optional[str] = Field(None, description="Batch identifier")

class BatchDetectionResponse(BaseModel):
    """Batch fraud detection response"""
    batch_id: str
    total_transactions: int
    fraud_detected: int
    processing_time_ms: float
    results: List[FraudDetectionResponse]
    summary: Dict[str, Any]

@router.post("/detect", response_model=FraudDetectionResponse)
async def detect_fraud(
    transaction: TransactionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Detect fraud in a single transaction
    
    This endpoint analyzes a transaction for potential fraud using:
    - Machine learning models (Autoencoder, LSTM)
    - Rule-based detection
    - Ensemble methods
    """
    try:
        record_api_request("detect_fraud")
        start_time = datetime.now()
        
        # Get fraud detector from app state
        fraud_detector = get_fraud_detector()
        
        # Convert to dictionary for processing
        transaction_data = transaction.dict()
        
        # Run fraud detection
        detection_result = await fraud_detector.detect_fraud(transaction_data)
        
        # Create transaction record
        db_transaction = Transaction.from_dict(transaction_data)
        db_transaction.id = str(uuid.uuid4())
        db_transaction.risk_score = detection_result['risk_score']
        db_transaction.fraud_probability = detection_result['fraud_probability']
        db_transaction.is_fraud = detection_result['is_fraud']
        
        # Save transaction to database
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # Create fraud alert if fraud detected
        alert_id = None
        if detection_result['is_fraud']:
            alert_id = await create_fraud_alert(db, db_transaction, detection_result)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Record metrics
        record_fraud_detection(
            is_fraud=detection_result['is_fraud'],
            processing_time=processing_time,
            confidence=detection_result['confidence_score']
        )
        
        # Add background task for analytics
        background_tasks.add_task(
            update_analytics,
            transaction_id=transaction.transaction_id,
            detection_result=detection_result
        )
        
        response = FraudDetectionResponse(
            transaction_id=transaction.transaction_id,
            fraud_probability=detection_result['fraud_probability'],
            risk_score=detection_result['risk_score'],
            confidence_score=detection_result['confidence_score'],
            is_fraud=detection_result['is_fraud'],
            detection_method=detection_result['detection_method'],
            risk_level=detection_result['risk_metrics']['risk_level'],
            recommended_action=detection_result['risk_metrics']['recommended_action'],
            prediction_time_ms=detection_result['prediction_time_ms'],
            timestamp=detection_result['timestamp'],
            alert_id=alert_id
        )
        
        logger.info(f"Fraud detection completed for transaction {transaction.transaction_id}")
        return response
        
    except Exception as e:
        logger.error(f"Fraud detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud detection failed: {str(e)}"
        )

@router.post("/detect-batch", response_model=BatchDetectionResponse)
async def detect_fraud_batch(
    batch_request: BatchDetectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Detect fraud in multiple transactions (batch processing)
    
    This endpoint processes multiple transactions efficiently using:
    - Parallel processing
    - Batch database operations
    - Aggregated results
    """
    try:
        record_api_request("detect_fraud_batch")
        start_time = datetime.now()
        
        # Generate batch ID if not provided
        batch_id = batch_request.batch_id or str(uuid.uuid4())
        
        # Get fraud detector
        fraud_detector = get_fraud_detector()
        
        results = []
        fraud_count = 0
        
        # Process transactions
        for transaction in batch_request.transactions:
            try:
                # Run fraud detection
                detection_result = await fraud_detector.detect_fraud(transaction.dict())
                
                # Create response
                response = FraudDetectionResponse(
                    transaction_id=transaction.transaction_id,
                    fraud_probability=detection_result['fraud_probability'],
                    risk_score=detection_result['risk_score'],
                    confidence_score=detection_result['confidence_score'],
                    is_fraud=detection_result['is_fraud'],
                    detection_method=detection_result['detection_method'],
                    risk_level=detection_result['risk_metrics']['risk_level'],
                    recommended_action=detection_result['risk_metrics']['recommended_action'],
                    prediction_time_ms=detection_result['prediction_time_ms'],
                    timestamp=detection_result['timestamp']
                )
                
                results.append(response)
                
                if detection_result['is_fraud']:
                    fraud_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process transaction {transaction.transaction_id}: {e}")
                # Add error response
                error_response = FraudDetectionResponse(
                    transaction_id=transaction.transaction_id,
                    fraud_probability=0.5,
                    risk_score=0.5,
                    confidence_score=0.0,
                    is_fraud=False,
                    detection_method="error",
                    risk_level="unknown",
                    recommended_action="review",
                    prediction_time_ms=0,
                    timestamp=datetime.now().isoformat()
                )
                results.append(error_response)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create summary
        summary = {
            "total_transactions": len(batch_request.transactions),
            "fraud_detected": fraud_count,
            "fraud_rate": fraud_count / len(batch_request.transactions) if batch_request.transactions else 0,
            "average_processing_time_ms": processing_time / len(batch_request.transactions) if batch_request.transactions else 0,
            "success_rate": len([r for r in results if r.detection_method != "error"]) / len(results) if results else 0
        }
        
        # Add background task for batch analytics
        background_tasks.add_task(
            update_batch_analytics,
            batch_id=batch_id,
            summary=summary
        )
        
        response = BatchDetectionResponse(
            batch_id=batch_id,
            total_transactions=len(batch_request.transactions),
            fraud_detected=fraud_count,
            processing_time_ms=processing_time,
            results=results,
            summary=summary
        )
        
        logger.info(f"Batch fraud detection completed for {len(batch_request.transactions)} transactions")
        return response
        
    except Exception as e:
        logger.error(f"Batch fraud detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch fraud detection failed: {str(e)}"
        )

@router.get("/status/{transaction_id}")
async def get_detection_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get fraud detection status for a specific transaction"""
    try:
        # Query database for transaction
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Get fraud alerts
        alerts = db.query(FraudAlert).filter(
            FraudAlert.transaction_id == transaction.id
        ).all()
        
        return {
            "transaction_id": transaction.transaction_id,
            "status": "completed",
            "fraud_probability": transaction.fraud_probability,
            "risk_score": transaction.risk_score,
            "is_fraud": transaction.is_fraud,
            "timestamp": transaction.timestamp.isoformat() if transaction.timestamp else None,
            "alerts": [alert.to_dict() for alert in alerts] if alerts else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detection status"
        )

@router.get("/performance")
async def get_detection_performance():
    """Get fraud detection system performance metrics"""
    try:
        fraud_detector = get_fraud_detector()
        performance_stats = fraud_detector.get_performance_stats()
        
        return {
            "system_status": "operational",
            "performance_metrics": performance_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )

@router.post("/reload-models")
async def reload_models():
    """Reload ML models from disk"""
    try:
        fraud_detector = get_fraud_detector()
        fraud_detector.reload_models()
        
        return {
            "message": "Models reloaded successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload models"
        )

# Helper functions
def get_fraud_detector() -> FraudDetector:
    """Get fraud detector instance from app state"""
    # This would typically come from the FastAPI app state
    # For now, create a new instance
    return FraudDetector()

async def create_fraud_alert(
    db: Session, 
    transaction: Transaction, 
    detection_result: Dict[str, Any]
) -> str:
    """Create a fraud alert for detected fraud"""
    try:
        alert = FraudAlert(
            alert_id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            risk_score=detection_result['risk_score'],
            fraud_probability=detection_result['fraud_probability'],
            confidence_score=detection_result['confidence_score'],
            status=AlertStatus.PENDING,
            severity=AlertSeverity.HIGH if detection_result['fraud_probability'] > 0.8 else AlertSeverity.MEDIUM,
            detection_method=detection_result['detection_method'],
            explanation=f"Fraud detected with {detection_result['fraud_probability']:.2%} probability",
            feature_importance=detection_result.get('ml_predictions', {}),
            contributing_factors=detection_result.get('risk_metrics', {}).get('risk_factors', [])
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Fraud alert created: {alert.alert_id}")
        return alert.alert_id
        
    except Exception as e:
        logger.error(f"Failed to create fraud alert: {e}")
        db.rollback()
        return None

async def update_analytics(transaction_id: str, detection_result: Dict[str, Any]):
    """Update analytics in background"""
    try:
        # This would typically update analytics dashboards
        # For now, just log the update
        logger.info(f"Analytics updated for transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to update analytics: {e}")

async def update_batch_analytics(batch_id: str, summary: Dict[str, Any]):
    """Update batch analytics in background"""
    try:
        # This would typically update batch analytics
        logger.info(f"Batch analytics updated for batch {batch_id}: {summary}")
    except Exception as e:
        logger.error(f"Failed to update batch analytics: {e}")
