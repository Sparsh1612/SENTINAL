"""
Schemas for transaction & fraud handling
Author: Sparsh
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid


class TxType(str, Enum):
    FOOD = "food"
    TRAVEL = "travel"
    SHOPPING = "shopping"
    UTILITIES = "utilities"
    HEALTH = "health"
    ONLINE = "online"
    OTHER = "other"


class Transaction(Base):
    """Transaction model for storing credit card transactions"""
    
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Transaction details
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    amount = Column(Float, nullable=False, index=True)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Card information
    card_id = Column(String(100), nullable=False, index=True)
    card_type = Column(String(50), nullable=True)
    card_brand = Column(String(50), nullable=True)
    
    # Merchant information
    merchant_id = Column(String(100), nullable=False, index=True)
    merchant_name = Column(String(200), nullable=True)
    merchant_category = Column(String(100), nullable=True)
    merchant_city = Column(String(100), nullable=True)
    merchant_country = Column(String(2), nullable=True)
    
    # Location information
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Transaction type
    transaction_type = Column(String(50), nullable=False, default='purchase')
    authorization_code = Column(String(100), nullable=True)
    
    # Risk indicators
    risk_score = Column(Float, nullable=True)
    fraud_probability = Column(Float, nullable=True)
    is_fraud = Column(Boolean, nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    fraud_alerts = relationship("FraudAlert", back_populates="transaction")
    feedback = relationship("Feedback", back_populates="transaction")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transactions_card_timestamp', 'card_id', 'timestamp'),
        Index('idx_transactions_merchant_timestamp', 'merchant_id', 'timestamp'),
        Index('idx_transactions_amount_timestamp', 'amount', 'timestamp'),
        Index('idx_transactions_risk_score', 'risk_score'),
        Index('idx_transactions_fraud_probability', 'fraud_probability'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, merchant={self.merchant_name})>"
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'amount': self.amount,
            'currency': self.currency,
            'card_id': self.card_id,
            'card_type': self.card_type,
            'card_brand': self.card_brand,
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant_name,
            'merchant_category': self.merchant_category,
            'merchant_city': self.merchant_city,
            'merchant_country': self.merchant_country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'ip_address': self.ip_address,
            'transaction_type': self.transaction_type,
            'authorization_code': self.authorization_code,
            'risk_score': self.risk_score,
            'fraud_probability': self.fraud_probability,
            'is_fraud': self.is_fraud,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create transaction from dictionary"""
        # Remove None values and convert to proper types
        clean_data = {k: v for k, v in data.items() if v is not None}
        
        # Handle timestamp conversion
        if 'timestamp' in clean_data and isinstance(clean_data['timestamp'], str):
            from datetime import datetime
            clean_data['timestamp'] = datetime.fromisoformat(clean_data['timestamp'])
        
        return cls(**clean_data)


class TxBase(BaseModel):
    tx_id: str
    user_ref: str
    amount: float = Field(..., gt=0)
    merchant: str
    category: TxType
    location: Optional[str]
    device: Optional[str]
    ip: Optional[str]


class TxCreate(TxBase):
    ts: Optional[datetime]


class TxRead(TxBase):
    id: int
    ts: datetime
    features: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class TxBatch(BaseModel):
    records: List[TxCreate]
    batch_ref: Optional[str]


class PredictionBase(BaseModel):
    model: str
    probability: float = Field(..., ge=0, le=1)
    flagged: bool
    confidence: Optional[float] = Field(None, ge=0, le=1)


class PredictionCreate(PredictionBase):
    tx_ref: int
    explain: Optional[Dict[str, Any]]


class PredictionRead(PredictionBase):
    id: int
    tx_ref: int
    ts: datetime
    explain: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class FeedbackBase(BaseModel):
    label: bool
    certainty: Optional[float] = Field(None, ge=0, le=1)
    notes: Optional[str]
    user_ref: Optional[str]


class FeedbackCreate(FeedbackBase):
    tx_ref: int


class FeedbackRead(FeedbackBase):
    id: int
    tx_ref: int
    ts: datetime

    class Config:
        from_attributes = True
