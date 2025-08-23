# plugins/examples/velocity_checker.py
"""
Velocity-based fraud detection plugin
Detects rapid successive transactions
Author: Sparsh
"""

from backend.core.plugin_system import BasePlugin
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class VelocityChecker(BasePlugin):
    """Detects fraud based on transaction velocity patterns"""
    
    def __init__(self):
        super().__init__()
        self.version = "1.2.0"
        self.author = "Sparsh"
        self.transaction_history = defaultdict(list)
        self.lock = threading.Lock()
        
        # Configuration
        self.max_transactions_per_hour = 10
        self.max_transactions_per_minute = 3
        self.velocity_threshold = 0.7
    
    def detect(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect velocity-based fraud patterns"""
        user_id = transaction.get('user_id')
        timestamp = transaction.get('timestamp')
        
        if not user_id or not timestamp:
            return None
        
        # Convert timestamp if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        with self.lock:
            # Clean old transactions (keep last 24 hours)
            cutoff_time = timestamp - timedelta(hours=24)
            self.transaction_history[user_id] = [
                t for t in self.transaction_history[user_id] 
                if t > cutoff_time
            ]
            
            # Add current transaction
            self.transaction_history[user_id].append(timestamp)
            
            # Check velocity patterns
            recent_transactions = self.transaction_history[user_id]
            
            # Check transactions in last hour
            hour_ago = timestamp - timedelta(hours=1)
            transactions_last_hour = sum(1 for t in recent_transactions if t > hour_ago)
            
            # Check transactions in last minute
            minute_ago = timestamp - timedelta(minutes=1)
            transactions_last_minute = sum(1 for t in recent_transactions if t > minute_ago)
            
            # Calculate risk scores
            hourly_risk = min(transactions_last_hour / self.max_transactions_per_hour, 1.0)
            minute_risk = min(transactions_last_minute / self.max_transactions_per_minute, 1.0)
            
            max_risk = max(hourly_risk, minute_risk)
            
            if max_risk > self.velocity_threshold:
                return {
                    'rule_triggered': 'velocity_check',
                    'score': max_risk,
                    'adjustment': 'increase',
                    'explanation': f'High velocity detected: {transactions_last_hour} transactions/hour, {transactions_last_minute} transactions/minute'
                }
        
        return None


