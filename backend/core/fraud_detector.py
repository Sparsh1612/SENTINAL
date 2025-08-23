import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
import joblib
import os
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..models.autoencoder import AutoencoderModel
from ..models.lstm import LSTMModel
from ..models.preprocessor import DataPreprocessor
from ..schemas.transaction import Transaction
from ..schemas.fraud import FraudAlert, AlertStatus, AlertSeverity
from ..config import settings
from ..utils.logger import setup_logger
from ..utils.metrics import record_prediction_time, record_model_accuracy

logger = setup_logger(__name__)

class FraudDetector:
    """Main fraud detection engine combining ML models and rule-based detection"""
    
    def __init__(self):
        self.logger = logger
        self.models = {}
        self.preprocessor = None
        self.rules = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize components
        self._load_models()
        self._load_preprocessor()
        self._load_rules()
        
        # Performance tracking
        self.prediction_count = 0
        self.avg_prediction_time = 0.0
        
    def _load_models(self):
        """Load trained ML models"""
        try:
            model_path = settings.MODEL_PATH
            
            # Load Autoencoder model
            autoencoder_path = os.path.join(model_path, "autoencoder.joblib")
            if os.path.exists(autoencoder_path):
                self.models['autoencoder'] = joblib.load(autoencoder_path)
                self.logger.info("Autoencoder model loaded successfully")
            
            # Load LSTM model
            lstm_path = os.path.join(model_path, "lstm.joblib")
            if os.path.exists(lstm_path):
                self.models['lstm'] = joblib.load(lstm_path)
                self.logger.info("LSTM model loaded successfully")
            
            # Load ensemble model
            ensemble_path = os.path.join(model_path, "ensemble.joblib")
            if os.path.exists(ensemble_path):
                self.models['ensemble'] = joblib.load(ensemble_path)
                self.logger.info("Ensemble model loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            # Initialize default models
            self.models['autoencoder'] = AutoencoderModel()
            self.models['lstm'] = LSTMModel()
    
    def _load_preprocessor(self):
        """Load data preprocessor"""
        try:
            preprocessor_path = os.path.join(settings.MODEL_PATH, "preprocessor.joblib")
            if os.path.exists(preprocessor_path):
                self.preprocessor = joblib.load(preprocessor_path)
                self.logger.info("Preprocessor loaded successfully")
            else:
                self.preprocessor = DataPreprocessor()
                self.logger.info("Initialized new preprocessor")
        except Exception as e:
            self.logger.error(f"Failed to load preprocessor: {e}")
            self.preprocessor = DataPreprocessor()
    
    def _load_rules(self):
        """Load rule-based detection rules"""
        try:
            # Basic fraud rules
            self.rules = [
                self._amount_threshold_rule,
                self._velocity_rule,
                self._location_rule,
                self._time_pattern_rule,
                self._merchant_risk_rule
            ]
            self.logger.info(f"Loaded {len(self.rules)} detection rules")
        except Exception as e:
            self.logger.error(f"Failed to load rules: {e}")
    
    async def detect_fraud(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main fraud detection method"""
        start_time = datetime.now()
        
        try:
            # Preprocess transaction data
            processed_data = self._preprocess_transaction(transaction_data)
            
            # Run ML model predictions
            ml_predictions = await self._run_ml_models(processed_data)
            
            # Run rule-based detection
            rule_predictions = await self._run_rules(transaction_data)
            
            # Combine predictions
            final_prediction = self._ensemble_predictions(ml_predictions, rule_predictions)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(final_prediction, transaction_data)
            
            # Record metrics
            prediction_time = (datetime.now() - start_time).total_seconds() * 1000
            record_prediction_time(prediction_time)
            
            # Update performance tracking
            self._update_performance_metrics(prediction_time)
            
            result = {
                'transaction_id': transaction_data.get('transaction_id'),
                'fraud_probability': final_prediction['fraud_probability'],
                'risk_score': final_prediction['risk_score'],
                'confidence_score': final_prediction['confidence_score'],
                'is_fraud': final_prediction['is_fraud'],
                'detection_method': final_prediction['method'],
                'ml_predictions': ml_predictions,
                'rule_predictions': rule_predictions,
                'risk_metrics': risk_metrics,
                'prediction_time_ms': prediction_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Fraud detection completed for transaction {transaction_data.get('transaction_id')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Fraud detection failed: {e}")
            raise
    
    def _preprocess_transaction(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """Preprocess transaction data for ML models"""
        try:
            if self.preprocessor:
                return self.preprocessor.transform(transaction_data)
            else:
                # Basic preprocessing if no preprocessor available
                return self._basic_preprocessing(transaction_data)
        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            return self._basic_preprocessing(transaction_data)
    
    def _basic_preprocessing(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """Basic data preprocessing"""
        # Extract numerical features
        features = []
        
        # Amount features
        amount = float(transaction_data.get('amount', 0))
        features.extend([amount, np.log1p(amount) if amount > 0 else 0])
        
        # Time features
        timestamp = transaction_data.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp)
            else:
                dt = timestamp
            
            features.extend([
                dt.hour,
                dt.weekday(),
                dt.month,
                dt.day
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Location features
        lat = float(transaction_data.get('latitude', 0))
        lon = float(transaction_data.get('longitude', 0))
        features.extend([lat, lon])
        
        # Categorical features (one-hot encoded)
        card_type = transaction_data.get('card_type', 'unknown')
        merchant_category = transaction_data.get('merchant_category', 'unknown')
        
        # Simple encoding for demo
        features.extend([
            1 if card_type == 'credit' else 0,
            1 if card_type == 'debit' else 0,
            1 if merchant_category == 'online' else 0,
            1 if merchant_category == 'retail' else 0
        ])
        
        return np.array(features).reshape(1, -1)
    
    async def _run_ml_models(self, processed_data: np.ndarray) -> Dict[str, Any]:
        """Run ML model predictions asynchronously"""
        predictions = {}
        
        try:
            # Run models in parallel
            tasks = []
            for model_name, model in self.models.items():
                task = asyncio.create_task(
                    self._predict_with_model(model_name, model, processed_data)
                )
                tasks.append(task)
            
            # Wait for all predictions
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, (model_name, _) in enumerate(self.models.items()):
                if isinstance(results[i], Exception):
                    self.logger.error(f"Model {model_name} prediction failed: {results[i]}")
                    predictions[model_name] = {'error': str(results[i])}
                else:
                    predictions[model_name] = results[i]
                    
        except Exception as e:
            self.logger.error(f"ML model prediction failed: {e}")
            predictions['error'] = str(e)
        
        return predictions
    
    async def _predict_with_model(self, model_name: str, model: Any, data: np.ndarray) -> Dict[str, Any]:
        """Predict with a single ML model"""
        try:
            # Run prediction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                self.executor, 
                model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                data
            )
            
            if hasattr(model, 'predict_proba'):
                # Classification model with probabilities
                fraud_prob = prediction[0][1] if len(prediction[0]) > 1 else prediction[0][0]
                return {
                    'fraud_probability': float(fraud_prob),
                    'confidence_score': float(fraud_prob),
                    'prediction': prediction.tolist()
                }
            else:
                # Regression model
                return {
                    'fraud_probability': float(prediction[0]),
                    'confidence_score': 0.8,  # Default confidence
                    'prediction': prediction.tolist()
                }
                
        except Exception as e:
            self.logger.error(f"Prediction with {model_name} failed: {e}")
            return {'error': str(e)}
    
    async def _run_rules(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run rule-based detection"""
        rule_results = {}
        
        try:
            for rule in self.rules:
                rule_name = rule.__name__
                try:
                    result = await rule(transaction_data)
                    rule_results[rule_name] = result
                except Exception as e:
                    self.logger.error(f"Rule {rule_name} failed: {e}")
                    rule_results[rule_name] = {'error': str(e)}
                    
        except Exception as e:
            self.logger.error(f"Rule-based detection failed: {e}")
            rule_results['error'] = str(e)
        
        return rule_results
    
    async def _amount_threshold_rule(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Amount threshold rule"""
        amount = float(transaction_data.get('amount', 0))
        
        # High amount threshold
        if amount > 10000:
            return {
                'triggered': True,
                'risk_score': 0.8,
                'reason': f'High amount: ${amount:,.2f}'
            }
        
        # Unusual amount patterns
        if amount > 5000:
            return {
                'triggered': True,
                'risk_score': 0.6,
                'reason': f'Unusual amount: ${amount:,.2f}'
            }
        
        return {
            'triggered': False,
            'risk_score': 0.1,
            'reason': 'Amount within normal range'
        }
    
    async def _velocity_rule(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transaction velocity rule"""
        # This would typically check against historical data
        # For now, return a basic assessment
        return {
            'triggered': False,
            'risk_score': 0.2,
            'reason': 'Velocity check passed'
        }
    
    async def _location_rule(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Location-based rule"""
        lat = transaction_data.get('latitude')
        lon = transaction_data.get('longitude')
        
        if lat is None or lon is None:
            return {
                'triggered': True,
                'risk_score': 0.7,
                'reason': 'Missing location data'
            }
        
        # Check for suspicious locations (simplified)
        if abs(lat) > 90 or abs(lon) > 180:
            return {
                'triggered': True,
                'risk_score': 0.9,
                'reason': 'Invalid coordinates'
            }
        
        return {
            'triggered': False,
            'risk_score': 0.1,
            'reason': 'Location data valid'
        }
    
    async def _time_pattern_rule(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Time pattern rule"""
        timestamp = transaction_data.get('timestamp')
        
        if not timestamp:
            return {
                'triggered': True,
                'risk_score': 0.6,
                'reason': 'Missing timestamp'
            }
        
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = timestamp
        
        # Check for unusual hours (2 AM - 5 AM)
        if 2 <= dt.hour <= 5:
            return {
                'triggered': True,
                'risk_score': 0.5,
                'reason': f'Unusual hour: {dt.hour}:00'
            }
        
        return {
            'triggered': False,
            'risk_score': 0.1,
            'reason': 'Normal time pattern'
        }
    
    async def _merchant_risk_rule(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merchant risk rule"""
        merchant_category = transaction_data.get('merchant_category', '').lower()
        
        # High-risk categories
        high_risk_categories = ['gambling', 'cryptocurrency', 'adult', 'pharmacy']
        
        if any(cat in merchant_category for cat in high_risk_categories):
            return {
                'triggered': True,
                'risk_score': 0.7,
                'reason': f'High-risk merchant category: {merchant_category}'
            }
        
        return {
            'triggered': False,
            'risk_score': 0.1,
            'reason': 'Standard merchant category'
        }
    
    def _ensemble_predictions(self, ml_predictions: Dict, rule_predictions: Dict) -> Dict[str, Any]:
        """Combine ML and rule-based predictions"""
        try:
            # Calculate ML ensemble
            ml_probs = []
            ml_confidences = []
            
            for model_name, pred in ml_predictions.items():
                if 'error' not in pred:
                    ml_probs.append(pred.get('fraud_probability', 0))
                    ml_confidences.append(pred.get('confidence_score', 0.5))
            
            # Calculate rule ensemble
            rule_scores = []
            for rule_name, pred in rule_predictions.items():
                if 'error' not in pred and pred.get('triggered', False):
                    rule_scores.append(pred.get('risk_score', 0))
            
            # Combine predictions
            if ml_probs:
                ml_fraud_prob = np.mean(ml_probs)
                ml_confidence = np.mean(ml_confidences)
            else:
                ml_fraud_prob = 0.5
                ml_confidence = 0.5
            
            if rule_scores:
                rule_risk_score = np.mean(rule_scores)
            else:
                rule_risk_score = 0.1
            
            # Weighted combination (ML: 70%, Rules: 30%)
            final_fraud_prob = 0.7 * ml_fraud_prob + 0.3 * rule_risk_score
            final_confidence = ml_confidence
            
            # Determine fraud status
            is_fraud = final_fraud_prob > settings.FRAUD_THRESHOLD
            
            return {
                'fraud_probability': float(final_fraud_prob),
                'risk_score': float(rule_risk_score),
                'confidence_score': float(final_confidence),
                'is_fraud': is_fraud,
                'method': 'ensemble'
            }
            
        except Exception as e:
            self.logger.error(f"Ensemble prediction failed: {e}")
            return {
                'fraud_probability': 0.5,
                'risk_score': 0.5,
                'confidence_score': 0.5,
                'is_fraud': False,
                'method': 'fallback'
            }
    
    def _calculate_risk_metrics(self, prediction: Dict, transaction_data: Dict) -> Dict[str, Any]:
        """Calculate additional risk metrics"""
        try:
            amount = float(transaction_data.get('amount', 0))
            
            # Risk factors
            risk_factors = []
            
            if amount > 10000:
                risk_factors.append('high_amount')
            
            if transaction_data.get('latitude') is None:
                risk_factors.append('missing_location')
            
            if transaction_data.get('ip_address') is None:
                risk_factors.append('missing_ip')
            
            # Calculate composite risk score
            base_risk = prediction.get('fraud_probability', 0.5)
            factor_multiplier = 1.0 + (len(risk_factors) * 0.1)
            composite_risk = min(1.0, base_risk * factor_multiplier)
            
            return {
                'composite_risk_score': float(composite_risk),
                'risk_factors': risk_factors,
                'risk_level': self._get_risk_level(composite_risk),
                'recommended_action': self._get_recommended_action(composite_risk)
            }
            
        except Exception as e:
            self.logger.error(f"Risk metrics calculation failed: {e}")
            return {
                'composite_risk_score': 0.5,
                'risk_factors': ['calculation_error'],
                'risk_level': 'medium',
                'recommended_action': 'review'
            }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level based on score"""
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _get_recommended_action(self, risk_score: float) -> str:
        """Get recommended action based on risk score"""
        if risk_score >= 0.8:
            return 'block'
        elif risk_score >= 0.6:
            return 'review'
        elif risk_score >= 0.4:
            return 'monitor'
        else:
            return 'approve'
    
    def _update_performance_metrics(self, prediction_time: float):
        """Update performance tracking metrics"""
        self.prediction_count += 1
        self.avg_prediction_time = (
            (self.avg_prediction_time * (self.prediction_count - 1) + prediction_time) 
            / self.prediction_count
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_predictions': self.prediction_count,
            'average_prediction_time_ms': self.avg_prediction_time,
            'models_loaded': list(self.models.keys()),
            'rules_loaded': len(self.rules),
            'preprocessor_loaded': self.preprocessor is not None
        }
    
    def reload_models(self):
        """Reload ML models from disk"""
        try:
            self._load_models()
            self.logger.info("Models reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload models: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.executor.shutdown(wait=True)
            self.logger.info("Fraud detector cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
