# backend/streaming/producer.py
"""
Kafka producer for real-time transaction streaming
Author: Sparsh
"""

from kafka import KafkaProducer
import json
import logging
from typing import Dict, Any
import asyncio

from ..config import get_settings

logger = logging.getLogger(__name__)


class KafkaTransactionProducer:
    """Kafka producer for streaming transactions"""
    
    def __init__(self):
        self.settings = get_settings()
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.settings.kafka.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=1000
            )
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.error(f"Error initializing Kafka producer: {e}")
            self.producer = None
    
    async def send_transaction(self, transaction_data: Dict[str, Any]):
        """Send transaction to Kafka topic"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            # Use transaction_id as key for partitioning
            key = transaction_data.get('transaction_id')
            
            future = self.producer.send(
                self.settings.kafka.topic_transactions,
                key=key,
                value=transaction_data
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            logger.debug(f"Transaction sent to Kafka: {key} -> {record_metadata.topic}:{record_metadata.partition}")
            
        except Exception as e:
            logger.error(f"Error sending transaction to Kafka: {e}")
    
    async def send_fraud_alert(self, alert_data: Dict[str, Any]):
        """Send fraud alert to Kafka topic"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            future = self.producer.send(
                self.settings.kafka.topic_alerts,
                value=alert_data
            )
            
            record_metadata = future.get(timeout=10)
            logger.info(f"Fraud alert sent to Kafka: {record_metadata.topic}:{record_metadata.partition}")
            
        except Exception as e:
            logger.error(f"Error sending fraud alert to Kafka: {e}")
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")