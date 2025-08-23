# backend/models/preprocessor.py
"""
Data preprocessing for fraud detection
Author: Sparsh
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from typing import Tuple, Dict, Any, Optional
import joblib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TransactionPreprocessor:
    """Advanced preprocessing for transaction data"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.is_fitted = False
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features from transaction data"""
        df = df.copy()
        
        # Time-based features
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        
        # Amount-based features
        df['amount_log'] = np.log1p(df['amount'])
        df['amount_rounded'] = (df['amount'] % 1 == 0).astype(int)
        
        # User behavior features (requires historical data)
        user_stats = df.groupby('user_id').agg({
            'amount': ['mean', 'std', 'min', 'max', 'count'],
            'merchant': 'nunique',
            'category': 'nunique'
        }).fillna(0)
        
        user_stats.columns = ['_'.join(col) for col in user_stats.columns]
        df = df.merge(user_stats, left_on='user_id', right_index=True, how='left')
        
        # Merchant frequency
        merchant_counts = df['merchant'].value_counts()
        df['merchant_frequency'] = df['merchant'].map(merchant_counts)
        df['merchant_rare'] = (df['merchant_frequency'] < 5).astype(int)
        
        # Velocity features (transactions per hour)
        df = df.sort_values(['user_id', 'timestamp'])
        df['time_since_last'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds() / 3600
        df['time_since_last'] = df['time_since_last'].fillna(24)  # Default 24 hours
        
        # Risk indicators
        df['high_amount'] = (df['amount'] > df['amount_mean'] + 2 * df['amount_std']).astype(int)
        df['velocity_risk'] = (df['time_since_last'] < 1).astype(int)  # Less than 1 hour
        
        return df
    
    def fit(self, df: pd.DataFrame) -> 'TransactionPreprocessor':
        """Fit preprocessor on training data"""
        logger.info("Fitting transaction preprocessor...")
        
        # Create features
        df_features = self.create_features(df)
        
        # Define feature columns
        numerical_features = [
            'amount', 'amount_log', 'hour', 'day_of_week',
            'amount_mean', 'amount_std', 'amount_min', 'amount_max',
            'merchant_frequency', 'time_since_last'
        ]
        
        categorical_features = ['merchant', 'category', 'location']
        
        # Fit scalers for numerical features
        for feature in numerical_features:
            if feature in df_features.columns:
                scaler = RobustScaler()
                scaler.fit(df_features[[feature]].fillna(0))
                self.scalers[feature] = scaler
        
        # Fit encoders for categorical features
        for feature in categorical_features:
            if feature in df_features.columns:
                encoder = LabelEncoder()
                encoder.fit(df_features[feature].fillna('unknown').astype(str))
                self.encoders[feature] = encoder
        
        # Store feature names
        self.feature_names = (
            numerical_features + 
            [f"{feat}_encoded" for feat in categorical_features] +
            ['is_weekend', 'is_night', 'amount_rounded', 'merchant_rare', 'high_amount', 'velocity_risk']
        )
        
        self.is_fitted = True
        logger.info(f"Preprocessor fitted with {len(self.feature_names)} features")
        return self
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform data using fitted preprocessor"""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transforming")
        
        df_features = self.create_features(df)
        transformed_features = []
        
        # Transform numerical features
        for feature, scaler in self.scalers.items():
            if feature in df_features.columns:
                scaled = scaler.transform(df_features[[feature]].fillna(0))
                transformed_features.append(scaled.ravel())
        
        # Transform categorical features
        for feature, encoder in self.encoders.items():
            if feature in df_features.columns:
                # Handle unseen categories
                feature_values = df_features[feature].fillna('unknown').astype(str)
                encoded = []
                for val in feature_values:
                    try:
                        encoded.append(encoder.transform([val])[0])
                    except ValueError:
                        encoded.append(encoder.transform(['unknown'])[0])
                transformed_features.append(np.array(encoded))
        
        # Add binary features
        binary_features = ['is_weekend', 'is_night', 'amount_rounded', 'merchant_rare', 'high_amount', 'velocity_risk']
        for feature in binary_features:
            if feature in df_features.columns:
                transformed_features.append(df_features[feature].values)
        
        return np.column_stack(transformed_features)
    
    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit and transform in one step"""
        return self.fit(df).transform(df)
    
    def save(self, filepath: str):
        """Save preprocessor to file"""
        joblib.dump({
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }, filepath)
        logger.info(f"Preprocessor saved to {filepath}")
    
    def load(self, filepath: str):
        """Load preprocessor from file"""
        data = joblib.load(filepath)
        self.scalers = data['scalers']
        self.encoders = data['encoders']
        self.feature_names = data['feature_names']
        self.is_fitted = data['is_fitted']
        logger.info(f"Preprocessor loaded from {filepath}")


def prepare_data_for_training(
    df: pd.DataFrame,
    target_column: str = 'is_fraud',
    test_size: float = 0.2,
    random_state: int = 42,
    balance_data: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, TransactionPreprocessor]:
    """Prepare data for model training"""
    
    logger.info("Preparing data for training...")
    
    # Initialize preprocessor
    preprocessor = TransactionPreprocessor()
    
    # Prepare features and target
    X = preprocessor.fit_transform(df)
    y = df[target_column].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Handle class imbalance with SMOTE
    if balance_data:
        logger.info("Applying SMOTE for class balancing...")
        smote = SMOTE(random_state=random_state)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        logger.info(f"After SMOTE - Fraud: {sum(y_train)}, Legitimate: {len(y_train) - sum(y_train)}")
    
    return X_train, X_test, y_train, y_test, preprocessor
