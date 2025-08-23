# backend/api/explanation.py
"""
Model explanation endpoints
Author: Sparsh
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ..database import get_db, Transaction, FraudPrediction
from ..core.explainer import ModelExplainer
from ..main import get_fraud_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/transaction/{transaction_id}/shap")
async def get_shap_explanation(
    transaction_id: str,
    db: Session = Depends(get_db),
    fraud_service = Depends(get_fraud_service)
):
    """Get SHAP explanation for a transaction"""
    try:
        # Find transaction
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get SHAP explanation
        explainer = ModelExplainer(fraud_service)
        explanation = await explainer.explain_shap(transaction_id)
        
        return {
            "transaction_id": transaction_id,
            "explanation_type": "shap",
            "feature_importance": explanation["feature_importance"],
            "base_value": explanation["base_value"],
            "prediction_value": explanation["prediction_value"],
            "explanation_data": explanation["explanation_data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}/lime")
async def get_lime_explanation(
    transaction_id: str,
    db: Session = Depends(get_db),
    fraud_service = Depends(get_fraud_service)
):
    """Get LIME explanation for a transaction"""
    try:
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        explainer = ModelExplainer(fraud_service)
        explanation = await explainer.explain_lime(transaction_id)
        
        return {
            "transaction_id": transaction_id,
            "explanation_type": "lime",
            "feature_importance": explanation["feature_importance"],
            "prediction_probability": explanation["prediction_probability"],
            "explanation_data": explanation["explanation_data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating LIME explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
