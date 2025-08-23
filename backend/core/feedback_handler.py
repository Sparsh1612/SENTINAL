# backend/core/feedback_handler.py
"""
Feedback processing for model improvement
Author: Sparsh
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..database import get_database_manager, FeedbackEntry, Transaction, FraudPrediction
from .fraud_detector import FraudDetectionService

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """Handles user feedback for model improvement"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.fraud_service = None
        self.feedback_threshold = 10  # Minimum feedback entries before retraining
    
    async def process_feedback(self, feedback_id: int):
        """Process a single feedback entry"""
        try:
            with self.db_manager.get_session() as session:
                feedback = session.query(FeedbackEntry).filter(
                    FeedbackEntry.id == feedback_id
                ).first()
                
                if not feedback:
                    logger.error(f"Feedback entry {feedback_id} not found")
                    return
                
                # Log feedback metrics
                await self._log_feedback_metrics(feedback, session)
                
                # Check if we should retrain models
                await self._check_retrain_trigger(session)
                
        except Exception as e:
            logger.error(f"Error processing feedback {feedback_id}: {e}")
    
    async def _log_feedback_metrics(self, feedback: FeedbackEntry, session: Session):
        """Log feedback metrics for monitoring"""
        # Get original prediction
        prediction = session.query(FraudPrediction).filter(
            FraudPrediction.transaction_id == feedback.transaction_id
        ).order_by(FraudPrediction.prediction_timestamp.desc()).first()
        
        if prediction:
            # Calculate agreement between model and user
            model_prediction = prediction.is_fraud
            user_label = feedback.user_label
            
            agreement = model_prediction == user_label
            
            logger.info(f"Feedback processed - Agreement: {agreement}, "
                       f"Model: {model_prediction}, User: {user_label}, "
                       f"Confidence: {feedback.confidence}")
    
    async def _check_retrain_trigger(self, session: Session):
        """Check if we should trigger model retraining"""
        # Count recent feedback entries
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_feedback_count = session.query(FeedbackEntry).filter(
            FeedbackEntry.feedback_timestamp >= week_ago
        ).count()
        
        if recent_feedback_count >= self.feedback_threshold:
            logger.info(f"Retraining trigger: {recent_feedback_count} feedback entries")
            await self._trigger_retraining(session)
    
    async def _trigger_retraining(self, session: Session):
        """Trigger model retraining with feedback data"""
        try:
            # Prepare training data with feedback
            training_data = await self._prepare_feedback_training_data(session)
            
            if len(training_data) < 100:  # Minimum data requirement
                logger.warning("Insufficient data for retraining")
                return
            
            # Initialize fraud service if needed
            if self.fraud_service is None:
                self.fraud_service = FraudDetectionService()
                await self.fraud_service.initialize()
            
            # Retrain models
            logger.info("Starting model retraining with feedback data...")
            metrics = await self.fraud_service.retrain_models(training_data)
            
            logger.info(f"Model retraining completed. New metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
    
    async def _prepare_feedback_training_data(self, session: Session) -> pd.DataFrame:
        """Prepare training data incorporating user feedback"""
        # Get transactions with feedback
        query = session.query(Transaction, FeedbackEntry).join(
            FeedbackEntry, Transaction.id == FeedbackEntry.transaction_id
        )
        
        transactions_with_feedback = query.all()
        
        training_records = []
        for transaction, feedback in transactions_with_feedback:
            record = {
                'transaction_id': transaction.transaction_id,
                'user_id': transaction.user_id,
                'amount': transaction.amount,
                'merchant': transaction.merchant,
                'category': transaction.category,
                'location': transaction.location,
                'device_id': transaction.device_id,
                'ip_address': transaction.ip_address,
                'timestamp': transaction.timestamp,
                'is_fraud': feedback.user_label  # Use user label as ground truth
            }
            training_records.append(record)
        
        return pd.DataFrame(training_records)