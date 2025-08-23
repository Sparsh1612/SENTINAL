"""
Database models and manager for Aegis
Author: Sparsh
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON,
    Text, ForeignKey, Index, MetaData
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncio

from .config import get_config, settings

logger = logging.getLogger("aegis.db")

Base = declarative_base()


class TxRecord(Base):
    __tablename__ = "tx_records"

    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String(60), unique=True, nullable=False)
    user_ref = Column(String(60), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    location = Column(String(120))
    device = Column(String(50))
    ip = Column(String(50))

    features = Column(JSON)

    predictions = relationship("PredictionLog", back_populates="tx")
    feedbacks = relationship("FeedbackLog", back_populates="tx")

    __table_args__ = (
        Index("ix_user_ts", "user_ref", "ts"),
        Index("ix_amt_ts", "amount", "ts"),
    )


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    tx_ref = Column(Integer, ForeignKey("tx_records.id"), nullable=False)
    model = Column(String(40), nullable=False)
    probability = Column(Float, nullable=False)
    flagged = Column(Boolean, nullable=False)
    confidence = Column(Float)
    ts = Column(DateTime(timezone=True), server_default=func.now())

    explain = Column(JSON)

    tx = relationship("TxRecord", back_populates="predictions")


class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id = Column(Integer, primary_key=True, index=True)
    tx_ref = Column(Integer, ForeignKey("tx_records.id"), nullable=False)
    label = Column(Boolean, nullable=False)
    certainty = Column(Float)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    user_ref = Column(String(50))

    tx = relationship("TxRecord", back_populates="feedbacks")


class MetricLog(Base):
    __tablename__ = "metric_logs"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(JSON)


class DBManager:
    """SQLAlchemy manager"""

    def __init__(self):
        cfg = get_config()
        self.engine = create_engine(
            cfg.postgres.dsn,
            echo=cfg.debug_mode,
            pool_pre_ping=True
        )
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def init_db(self):
        Base.metadata.create_all(self.engine)
        logger.info("Database schema ready.")

    @contextmanager
    def session_scope(self) -> Generator:
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as ex:
            session.rollback()
            logger.error(f"Session error: {ex}")
            raise
        finally:
            session.close()


# Singleton DB accessor
_db: Optional[DBManager] = None

def get_db_manager() -> DBManager:
    global _db
    if _db is None:
        _db = DBManager()
    return _db


# Create logger
logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
Base = declarative_base()

# Metadata for database operations
metadata = MetaData()

async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from .schemas import fraud, transaction, feedback
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def create_indexes():
    """Create database indexes for performance"""
    try:
        # Create indexes for common queries
        with engine.connect() as conn:
            # Transaction indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_timestamp 
                ON transactions (timestamp);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_card_id 
                ON transactions (card_id);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_amount 
                ON transactions (amount);
            """)
            
            # Fraud alert indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fraud_alerts_timestamp 
                ON fraud_alerts (timestamp);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status 
                ON fraud_alerts (status);
            """)
            
            # Feedback indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_transaction_id 
                ON feedback (transaction_id);
            """)
            
            conn.commit()
            
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_db_async() -> Session:
    """Get database session asynchronously"""
    loop = asyncio.get_event_loop()
    db = await loop.run_in_executor(None, SessionLocal)
    try:
        return db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await loop.run_in_executor(None, db.rollback)
        raise

def close_db(db: Session):
    """Close database session"""
    try:
        db.close()
    except Exception as e:
        logger.error(f"Error closing database session: {e}")

# Database health check
def check_db_health() -> bool:
    """Check database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Database statistics
def get_db_stats() -> dict:
    """Get database statistics"""
    try:
        with engine.connect() as conn:
            # Get table counts
            result = conn.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            
            stats = {
                "tables": [dict(row) for row in result],
                "connection_pool": {
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}
