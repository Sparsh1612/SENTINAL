# backend/core/explainer.py
"""
Model explanation service using SHAP and LIME
Author: Sparsh
"""

import shap
import lime
import lime.tabular
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

from .fraud_detector import FraudDetectionService
from ..database import get_database_manager, Transaction

logger = logging.getLogger(__name__)


class ModelExplainer:
    """Service for explaining model predictions"""
    
    def __init__(self, fraud_service: FraudDetectionService):
        self.fraud_service = fraud_service
        self.shap_explainer = None
        self.lime_explainer = None
        self._initialize_explainers()
    
    def _initialize_explainers(self):
        """Initialize SHAP and LIME explainers"""
        try:
            if self.fraud_service.preprocessor is None:
                logger.warning("Preprocessor not available for explanation")
                return
            
            # Initialize SHAP explainer for the ensemble model
            if self.fraud_service.lstm_model is not None:
                # Use a sample of data to initialize explainer
                # In practice, you'd use a representative background dataset
                background_data = np.random.random((100, len(self.fraud_service.preprocessor.feature_names)))
                self.shap_explainer = shap.KernelExplainer(
                    self._predict_for_shap, 
                    background_data
                )
            
            logger.info("Model explainers initialized")
            
        except Exception as e:
            logger.error(f"Error initializing explainers: {e}")
    
    def _predict_for_shap(self, X: np.ndarray) -> np.ndarray:
        """Prediction function for SHAP"""
        try:
            predictions = []
            for i in range(X.shape[0]):
                # Create a single transaction DataFrame
                transaction_data = pd.DataFrame([X[i]], columns=self.fraud_service.preprocessor.feature_names)
                result = asyncio.run(self.fraud_service.predict_fraud(transaction_data))
                predictions.append(result['fraud_probability'])
            return np.array(predictions)
        except Exception as e:
            logger.error(f"Error in SHAP prediction function: {e}")
            return np.zeros(X.shape[0])
    
    async def explain_shap(self, transaction_id: str) -> Dict[str, Any]:
        """Generate SHAP explanation for a transaction"""
        try:
            # Get transaction data
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                transaction = session.query(Transaction).filter(
                    Transaction.transaction_id == transaction_id
                ).first()
                
                if not transaction:
                    raise ValueError(f"Transaction {transaction_id} not found")
                
                # Convert to DataFrame and preprocess
                transaction_df = pd.DataFrame([{
                    'transaction_id': transaction.transaction_id,
                    'user_id': transaction.user_id,
                    'amount': transaction.amount,
                    'merchant': transaction.merchant,
                    'category': transaction.category,
                    'location': transaction.location,
                    'device_id': transaction.device_id,
                    'ip_address': transaction.ip_address,
                    'timestamp': transaction.timestamp
                }])
                
                X = self.fraud_service.preprocessor.transform(transaction_df)
                
                # Generate SHAP values
                if self.shap_explainer is not None:
                    shap_values = self.shap_explainer.shap_values(X[0:1])
                    
                    # Create feature importance dictionary
                    feature_names = self.fraud_service.preprocessor.feature_names
                    feature_importance = dict(zip(
                        feature_names,
                        shap_values[0].tolist()
                    ))
                    
                    return {
                        'transaction_id': transaction_id,
                        'feature_importance': feature_importance,
                        'base_value': float(self.shap_explainer.expected_value),
                        'prediction_value': float(shap_values[0].sum() + self.shap_explainer.expected_value),
                        'explanation_data': {
                            'method': 'shap',
                            'top_features': sorted(
                                feature_importance.items(),
                                key=lambda x: abs(x[1]),
                                reverse=True
                            )[:10]
                        }
                    }
                else:
                    raise RuntimeError("SHAP explainer not initialized")
                    
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            raise
    
    async def explain_lime(self, transaction_id: str) -> Dict[str, Any]:
        """Generate LIME explanation for a transaction"""
        try:
            # Get transaction data (similar to SHAP)
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                transaction = session.query(Transaction).filter(
                    Transaction.transaction_id == transaction_id
                ).first()
                
                if not transaction:
                    raise ValueError(f"Transaction {transaction_id} not found")
                
                # Convert and preprocess
                transaction_df = pd.DataFrame([{
                    'transaction_id': transaction.transaction_id,
                    'user_id': transaction.user_id,
                    'amount': transaction.amount,
                    'merchant': transaction.merchant,
                    'category': transaction.category,
                    'location': transaction.location,
                    'device_id': transaction.device_id,
                    'ip_address': transaction.ip_address,
                    'timestamp': transaction.timestamp
                }])
                
                X = self.fraud_service.preprocessor.transform(transaction_df)
                
                # Initialize LIME explainer if not done
                if self.lime_explainer is None:
                    # Use sample data for LIME training
                    training_data = np.random.random((1000, X.shape[1]))
                    self.lime_explainer = lime.tabular.LimeTabularExplainer(
                        training_data,
                        feature_names=self.fraud_service.preprocessor.feature_names,
                        class_names=['Legitimate', 'Fraud'],
                        mode='classification'
                    )
                
                # Generate LIME explanation
                explanation = self.lime_explainer.explain_instance(
                    X[0],
                    self._predict_for_lime,
                    num_features=10
                )
                
                # Extract feature importance
                feature_importance = dict(explanation.as_list())
                
                return {
                    'transaction_id': transaction_id,
                    'feature_importance': feature_importance,
                    'prediction_probability': explanation.predict_proba[1],  # Fraud probability
                    'explanation_data': {
                        'method': 'lime',
                        'local_explanation': explanation.as_list()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {e}")
            raise
    
    def _predict_for_lime(self, X: np.ndarray) -> np.ndarray:
        """Prediction function for LIME"""
        try:
            probabilities = []
            for i in range(X.shape[0]):
                transaction_data = pd.DataFrame([X[i]], columns=self.fraud_service.preprocessor.feature_names)
                result = asyncio.run(self.fraud_service.predict_fraud(transaction_data))
                fraud_prob = result['fraud_probability']
                probabilities.append([1 - fraud_prob, fraud_prob])  # [legit_prob, fraud_prob]
            return np.array(probabilities)
        except Exception as e:
            logger.error(f"Error in LIME prediction function: {e}")
            return np.array([[0.5, 0.5]] * X.shape[0])

