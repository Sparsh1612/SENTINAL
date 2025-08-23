from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid
import enum

class AlertStatus(enum.Enum):
    """Fraud alert status enumeration"""
    PENDING = "pending"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class AlertSeverity(enum.Enum):
    """Fraud alert severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FraudAlert(Base):
    """Fraud alert model for storing fraud detection results"""
    
    __tablename__ = "fraud_alerts"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Alert details
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Transaction reference
    transaction_id = Column(String(100), ForeignKey("transactions.id"), nullable=False, index=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False, index=True)
    fraud_probability = Column(Float, nullable=False, index=True)
    confidence_score = Column(Float, nullable=True)
    
    # Alert classification
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.PENDING, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.MEDIUM, index=True)
    
    # Detection details
    detection_method = Column(String(100), nullable=False)  # ML model, rule-based, etc.
    model_version = Column(String(50), nullable=True)
    rule_name = Column(String(100), nullable=True)
    
    # Explanation and reasoning
    explanation = Column(Text, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    
    # User actions
    assigned_to = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="fraud_alerts")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fraud_alerts_status_timestamp', 'status', 'timestamp'),
        Index('idx_fraud_alerts_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_fraud_alerts_risk_score', 'risk_score'),
        Index('idx_fraud_alerts_assigned_to', 'assigned_to'),
    )
    
    def __repr__(self):
        return f"<FraudAlert(id={self.id}, status={self.status}, severity={self.severity})>"
    
    def to_dict(self):
        """Convert fraud alert to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'transaction_id': self.transaction_id,
            'risk_score': self.risk_score,
            'fraud_probability': self.fraud_probability,
            'confidence_score': self.confidence_score,
            'status': self.status.value if self.status else None,
            'severity': self.severity.value if self.severity else None,
            'detection_method': self.detection_method,
            'model_version': self.model_version,
            'rule_name': self.rule_name,
            'explanation': self.explanation,
            'feature_importance': self.feature_importance,
            'contributing_factors': self.contributing_factors,
            'assigned_to': self.assigned_to,
            'notes': self.notes,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create fraud alert from dictionary"""
        # Remove None values and convert to proper types
        clean_data = {k: v for k, v in data.items() if v is not None}
        
        # Handle timestamp conversion
        if 'timestamp' in clean_data and isinstance(clean_data['timestamp'], str):
            from datetime import datetime
            clean_data['timestamp'] = datetime.fromisoformat(clean_data['timestamp'])
        
        # Handle enum conversion
        if 'status' in clean_data and isinstance(clean_data['status'], str):
            clean_data['status'] = AlertStatus(clean_data['status'])
        
        if 'severity' in clean_data and isinstance(clean_data['severity'], str):
            clean_data['severity'] = AlertSeverity(clean_data['severity'])
        
        return cls(**clean_data)
    
    def update_status(self, new_status: AlertStatus, notes: str = None):
        """Update alert status with optional notes"""
        self.status = new_status
        if notes:
            self.notes = notes
        
        if new_status in [AlertStatus.RESOLVED, AlertStatus.CONFIRMED, AlertStatus.FALSE_POSITIVE]:
            from datetime import datetime
            self.resolved_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def assign_to(self, user_id: str):
        """Assign alert to a user"""
        self.assigned_to = user_id
        self.updated_at = datetime.utcnow()
    
    def add_note(self, note: str):
        """Add a note to the alert"""
        if self.notes:
            self.notes += f"\n{datetime.utcnow()}: {note}"
        else:
            self.notes = f"{datetime.utcnow()}: {note}"
        self.updated_at = datetime.utcnow()
