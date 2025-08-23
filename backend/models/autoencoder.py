import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AutoencoderModel:
    """Autoencoder model for anomaly detection in credit card transactions"""
    
    def __init__(self, input_dim: int = 20, encoding_dim: int = 8, 
                 hidden_dims: list = None, learning_rate: float = 0.001):
        """
        Initialize Autoencoder model
        
        Args:
            input_dim: Number of input features
            encoding_dim: Dimension of the encoded representation
            hidden_dims: List of hidden layer dimensions
            learning_rate: Learning rate for training
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.hidden_dims = hidden_dims or [16, 12]
        self.learning_rate = learning_rate
        
        # Model components
        self.encoder = None
        self.decoder = None
        self.scaler = StandardScaler()
        self.threshold = None
        
        # Training history
        self.training_history = {
            'loss': [],
            'val_loss': [],
            'reconstruction_error': []
        }
        
        # Performance metrics
        self.performance_metrics = {}
        
        # Initialize model
        self._build_model()
    
    def _build_model(self):
        """Build the autoencoder architecture"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            
            # Encoder
            encoder_input = keras.layers.Input(shape=(self.input_dim,))
            x = encoder_input
            
            for dim in self.hidden_dims:
                x = keras.layers.Dense(dim, activation='relu')(x)
                x = keras.layers.BatchNormalization()(x)
                x = keras.layers.Dropout(0.2)(x)
            
            encoded = keras.layers.Dense(self.encoding_dim, activation='relu', name='encoded')(x)
            
            # Decoder
            x = encoded
            for dim in reversed(self.hidden_dims):
                x = keras.layers.Dense(dim, activation='relu')(x)
                x = keras.layers.BatchNormalization()(x)
                x = keras.layers.Dropout(0.2)(x)
            
            decoded = keras.layers.Dense(self.input_dim, activation='linear', name='decoded')(x)
            
            # Create models
            self.encoder = keras.Model(encoder_input, encoded, name='encoder')
            self.autoencoder = keras.Model(encoder_input, decoded, name='autoencoder')
            
            # Compile
            optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
            self.autoencoder.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
            
            logger.info("Autoencoder model built successfully")
            
        except ImportError:
            logger.warning("TensorFlow not available, using scikit-learn implementation")
            self._build_sklearn_model()
    
    def _build_sklearn_model(self):
        """Build scikit-learn based autoencoder (fallback)"""
        from sklearn.neural_network import MLPRegressor
        
        self.autoencoder = MLPRegressor(
            hidden_layer_sizes=self.hidden_dims + [self.encoding_dim] + list(reversed(self.hidden_dims)),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=self.learning_rate,
            max_iter=1000,
            random_state=42
        )
        
        logger.info("Scikit-learn autoencoder model built successfully")
    
    def preprocess_data(self, data: np.ndarray) -> np.ndarray:
        """Preprocess input data"""
        try:
            # Handle different input types
            if isinstance(data, pd.DataFrame):
                data = data.values
            elif isinstance(data, list):
                data = np.array(data)
            
            # Ensure 2D array
            if data.ndim == 1:
                data = data.reshape(1, -1)
            
            # Scale data
            if hasattr(self.scaler, 'fit_transform'):
                # First time - fit and transform
                data_scaled = self.scaler.fit_transform(data)
            else:
                # Transform only
                data_scaled = self.scaler.transform(data)
            
            return data_scaled
            
        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            return data
    
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None, 
            validation_split: float = 0.2, epochs: int = 100, 
            batch_size: int = 32, verbose: int = 1) -> Dict[str, Any]:
        """
        Train the autoencoder model
        
        Args:
            X: Training data
            y: Target values (not used for autoencoder)
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level
            
        Returns:
            Training history
        """
        try:
            # Preprocess data
            X_processed = self.preprocess_data(X)
            
            # Split data
            split_idx = int(len(X_processed) * (1 - validation_split))
            X_train = X_processed[:split_idx]
            X_val = X_processed[split_idx:]
            
            logger.info(f"Training autoencoder with {len(X_train)} samples")
            
            # Train model
            if hasattr(self.autoencoder, 'fit'):
                if hasattr(self.autoencoder, 'fit'):
                    # TensorFlow model
                    history = self.autoencoder.fit(
                        X_train, X_train,
                        validation_data=(X_val, X_val),
                        epochs=epochs,
                        batch_size=batch_size,
                        verbose=verbose,
                        callbacks=[
                            keras.callbacks.EarlyStopping(
                                monitor='val_loss',
                                patience=10,
                                restore_best_weights=True
                            )
                        ]
                    )
                    
                    # Store history
                    self.training_history['loss'] = history.history['loss']
                    self.training_history['val_loss'] = history.history['val_loss']
                    
                else:
                    # Scikit-learn model
                    self.autoencoder.fit(X_train, X_train)
                    
                    # Calculate validation loss
                    X_val_pred = self.autoencoder.predict(X_val)
                    val_loss = mean_squared_error(X_val, X_val_pred)
                    self.training_history['val_loss'] = [val_loss]
            
            # Calculate reconstruction error threshold
            self._calculate_threshold(X_train)
            
            # Calculate performance metrics
            self._calculate_performance_metrics(X_train, X_val)
            
            logger.info("Autoencoder training completed successfully")
            return self.training_history
            
        except Exception as e:
            logger.error(f"Autoencoder training failed: {e}")
            raise
    
    def _calculate_threshold(self, X: np.ndarray):
        """Calculate reconstruction error threshold for anomaly detection"""
        try:
            # Get reconstruction errors
            X_reconstructed = self.predict(X)
            reconstruction_errors = np.mean(np.square(X - X_reconstructed), axis=1)
            
            # Calculate threshold (95th percentile)
            self.threshold = np.percentile(reconstruction_errors, 95)
            
            logger.info(f"Reconstruction error threshold: {self.threshold:.6f}")
            
        except Exception as e:
            logger.error(f"Threshold calculation failed: {e}")
            self.threshold = 0.1  # Default threshold
    
    def _calculate_performance_metrics(self, X_train: np.ndarray, X_val: np.ndarray):
        """Calculate model performance metrics"""
        try:
            # Training metrics
            X_train_pred = self.predict(X_train)
            train_mse = mean_squared_error(X_train, X_train_pred)
            train_mae = mean_absolute_error(X_train, X_train_pred)
            
            # Validation metrics
            X_val_pred = self.predict(X_val)
            val_mse = mean_squared_error(X_val, X_val_pred)
            val_mae = mean_absolute_error(X_val, X_val_pred)
            
            self.performance_metrics = {
                'train_mse': train_mse,
                'train_mae': train_mae,
                'val_mse': val_mse,
                'val_mae': val_mae,
                'threshold': self.threshold
            }
            
            logger.info(f"Performance metrics calculated - Train MSE: {train_mse:.6f}, Val MSE: {val_mse:.6f}")
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions (reconstructions)"""
        try:
            # Preprocess data
            X_processed = self.preprocess_data(X)
            
            # Generate predictions
            if hasattr(self.autoencoder, 'predict'):
                predictions = self.autoencoder.predict(X_processed)
            else:
                # For scikit-learn models
                predictions = self.autoencoder.predict(X_processed)
                # Reshape if needed
                if predictions.ndim == 1:
                    predictions = predictions.reshape(-1, 1)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return X_processed
    
    def detect_anomalies(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies using reconstruction error
        
        Args:
            X: Input data
            
        Returns:
            Tuple of (anomaly_scores, is_anomaly)
        """
        try:
            # Get reconstructions
            X_reconstructed = self.predict(X)
            
            # Calculate reconstruction errors
            reconstruction_errors = np.mean(np.square(X - X_reconstructed), axis=1)
            
            # Determine anomalies
            is_anomaly = reconstruction_errors > self.threshold
            
            return reconstruction_errors, is_anomaly
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            # Return default values
            return np.zeros(len(X)), np.zeros(len(X), dtype=bool)
    
    def get_anomaly_score(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores for input data"""
        try:
            # Get reconstructions
            X_reconstructed = self.predict(X)
            
            # Calculate reconstruction errors
            reconstruction_errors = np.mean(np.square(X - X_reconstructed), axis=1)
            
            # Normalize scores to [0, 1] range
            if self.threshold:
                normalized_scores = np.clip(reconstruction_errors / self.threshold, 0, 1)
            else:
                normalized_scores = reconstruction_errors
            
            return normalized_scores
            
        except Exception as e:
            logger.error(f"Anomaly score calculation failed: {e}")
            return np.zeros(len(X))
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save model
            if hasattr(self.autoencoder, 'save'):
                # TensorFlow model
                self.autoencoder.save(filepath)
            else:
                # Scikit-learn model
                joblib.dump(self.autoencoder, filepath)
            
            # Save scaler and other components
            scaler_path = filepath.replace('.joblib', '_scaler.joblib')
            joblib.dump(self.scaler, scaler_path)
            
            # Save metadata
            metadata = {
                'input_dim': self.input_dim,
                'encoding_dim': self.encoding_dim,
                'hidden_dims': self.hidden_dims,
                'threshold': self.threshold,
                'performance_metrics': self.performance_metrics
            }
            
            metadata_path = filepath.replace('.joblib', '_metadata.joblib')
            joblib.dump(metadata, metadata_path)
            
            logger.info(f"Model saved successfully to {filepath}")
            
        except Exception as e:
            logger.error(f"Model saving failed: {e}")
            raise
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        try:
            # Load main model
            if filepath.endswith('.joblib'):
                self.autoencoder = joblib.load(filepath)
            else:
                # TensorFlow model
                import tensorflow as tf
                self.autoencoder = tf.keras.models.load_model(filepath)
            
            # Load scaler
            scaler_path = filepath.replace('.joblib', '_scaler.joblib')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            
            # Load metadata
            metadata_path = filepath.replace('.joblib', '_metadata.joblib')
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                self.input_dim = metadata.get('input_dim', self.input_dim)
                self.encoding_dim = metadata.get('encoding_dim', self.encoding_dim)
                self.hidden_dims = metadata.get('hidden_dims', self.hidden_dims)
                self.threshold = metadata.get('threshold', self.threshold)
                self.performance_metrics = metadata.get('performance_metrics', {})
            
            logger.info(f"Model loaded successfully from {filepath}")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get model summary information"""
        return {
            'model_type': 'Autoencoder',
            'input_dim': self.input_dim,
            'encoding_dim': self.encoding_dim,
            'hidden_dims': self.hidden_dims,
            'learning_rate': self.learning_rate,
            'threshold': self.threshold,
            'performance_metrics': self.performance_metrics,
            'training_history': self.training_history
        }
