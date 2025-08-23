# backend/api/feedback.py
"""
Feedback endpoints for model improvement
Author: Sparsh
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from ..database import get_db, Transaction, FeedbackEntry
from ..schemas.transaction import FeedbackCreate, FeedbackInDB
from ..core.feedback_handler import FeedbackHandler

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/submit", response_model=Dict[str, Any])
async def submit_feedback(
    feedback: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit user feedback for a transaction"""
    try:
        # Verify transaction exists
        transaction = db.query(Transaction).filter(
            Transaction.id == feedback.transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Create feedback entry
        db_feedback = FeedbackEntry(
            transaction_id=feedback.transaction_id,
            user_label=feedback.user_label,
            confidence=feedback.confidence,
            comments=feedback.comments,
            user_id=feedback.user_id
        )
        
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        # Process feedback in background
        background_tasks.add_task(
            process_feedback_async,
            db_feedback.id
        )
        
        logger.info(f"Feedback submitted for transaction {feedback.transaction_id}")
        
        return {
            "status": "success",
            "feedback_id": db_feedback.id,
            "message": "Feedback submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}", response_model=List[FeedbackInDB])
async def get_transaction_feedback(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get all feedback for a transaction"""
    feedback_entries = db.query(FeedbackEntry).filter(
        FeedbackEntry.transaction_id == transaction_id
    ).all()
    
    return feedback_entries


async def process_feedback_async(feedback_id: int):
    """Process feedback asynchronously"""
    try:
        handler = FeedbackHandler()
        await handler.process_feedback(feedback_id)
        logger.info(f"Feedback {feedback_id} processed successfully")
    except Exception as e:
        logger.error(f"Error processing feedback {feedback_id}: {e}")


