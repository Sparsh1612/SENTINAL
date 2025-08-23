# backend/streaming/consumer.py
"""
Kafka consumer for real-time fraud detection
Author: Sparsh
"""

from kafka import KafkaConsumer
import json
import logging
import asyncio
from typing import Dict, Any

from ..config import get_settings
from ..core.fraud_detector import FraudDetectionService

logger = logging.getLogger(__name__)


class KafkaTransactionConsumer:
    """Kafka consumer for processing transactions in real-time"""
    
    def __init__(self):
        self.settings = get_settings()
        self.consumer = None
        self.fraud_service = None
        self.running = False
    
    async def initialize(self):
        """Initialize consumer and fraud detection service"""
        try:
            self.consumer = KafkaConsumer(
                self.settings.kafka.topic_transactions,
                bootstrap_servers=self.settings.kafka.bootstrap_servers.split(','),
                group_id=self.settings.kafka.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            self.fraud_service = FraudDetectionService()
            await self.fraud_service.initialize()
            
            logger.info("Kafka consumer initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Kafka consumer: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming messages from Kafka"""
        if not self.consumer or not self.fraud_service:
            await self.initialize()
        
        self.running = True
        logger.info("Starting Kafka message consumption...")
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            await self._process_transaction(message.value)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            self.stop()
    
    async def _process_transaction(self, transaction_data: Dict[str, Any]):
        """Process a single transaction for fraud detection"""
        try:
            # Perform fraud detection
            result = await self.fraud_service.predict_fraud(transaction_data)
            
            # If fraud detected, send alert
            if result['is_fraud']:
                alert_data = {
                    'transaction_id': transaction_data.get('transaction_id'),
                    'user_id': transaction_data.get('user_id'),
                    'amount': transaction_data.get('amount'),
                    'merchant': transaction_data.get('merchant'),
                    'fraud_probability': result['fraud_probability'],
                    'risk_level': result['risk_level'],
                    'timestamp': result['timestamp']
                }
                
                # Send alert (could be to another Kafka topic, database, or notification service)
                logger.warning(f"FRAUD DETECTED: {alert_data}")
                
                # Here you could send to alerts topic
                # await self._send_alert(alert_data)
        
        except Exception as e:
            logger.error(f"Error processing transaction {transaction_data.get('transaction_id', 'unknown')}: {e}")
    
    def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer stopped")