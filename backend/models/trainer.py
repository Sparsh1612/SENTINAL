# backend/models/trainer.py
"""
Model training orchestrator
Author: Sparsh (refactor)
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score
)
import logging
import os
from typing import Dict, Any
import joblib

from .preprocessor import TransactionPreprocessor, prepare_data_for_training
from .autoencoder import FraudAutoencoder
from .lstm import FraudLSTM
from ..config import get_settings

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Orchestrates training of fraud detection models."""

    def __init__(self):
        self.settings = get_settings()
        self.preprocessor: TransactionPreprocessor = None
        self.autoencoder: FraudAutoencoder = None
        self.lstm_model: FraudLSTM = None
        self.metrics: Dict[str, Any] = {}

    def train_models(self, df: pd.DataFrame, target_column: str = "is_fraud") -> Dict[str, Any]:
        """Train all fraud detection models."""
        logger.info("Starting model training pipeline...")

        # Leakage-safe split & transform inside helper
        X_train, X_test, y_train, y_test, self.preprocessor = prepare_data_for_training(
            df, target_column=target_column, test_size=0.2, balance_data=True
        )

        # === Autoencoder (unsupervised): train only on normal transactions ===
        logger.info("Training Autoencoder...")
        normal_mask = y_train == 0
        X_train_normal = X_train[normal_mask]

        # Validation on normal portion of test
        X_test_normal = X_test[y_test == 0]

        self.autoencoder = FraudAutoencoder(
            input_dim=X_train.shape[1],
            encoding_dim=32,
            hidden_layers=[128, 64, 32],
            dropout=0.2
        )

        self.autoencoder.fit(
            X_train_normal,
            X_val=X_test_normal if len(X_test_normal) > 0 else None,
            epochs=self.settings.ml.epochs,
            batch_size=self.settings.ml.batch_size
        )

        # Threshold from train-normal
        self.autoencoder.calculate_threshold(X_train_normal, contamination=0.1)

        # === LSTM (supervised) ===
        logger.info("Training LSTM...")
        # Optional class weights (heavier weight for fraud)
        pos = max(1, int(y_train.sum()))
        neg = max(1, int(len(y_train) - pos))
        cw = {0: 1.0, 1: max(1.0, neg / pos)}  # inverse frequency

        self.lstm_model = FraudLSTM(
            input_dim=X_train.shape[1],
            sequence_length=10,
            lstm_units=[64, 32],
            dropout=0.3,
            class_weight=cw
        )

        self.lstm_model.fit(
            X_train, y_train,
            X_val=X_test, y_val=y_test,
            epochs=self.settings.ml.epochs,
            batch_size=self.settings.ml.batch_size
        )

        # Evaluate
        self.metrics = self.evaluate_models(X_test, y_test)

        # Save artifacts
        self.save_models()

        logger.info("Model training completed successfully.")
        return self.metrics

    def evaluate_models(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluate trained models."""
        metrics: Dict[str, Any] = {}

        # Autoencoder
        logger.info("Evaluating Autoencoder...")
        ae_pred, ae_scores = self.autoencoder.predict_anomaly(X_test)

        ae_report = classification_report(
            y_test, ae_pred, output_dict=True, zero_division=0
        )
        ae_auc = roc_auc_score(y_test, ae_scores) if len(np.unique(y_test)) > 1 else 0.0
        ae_pr = average_precision_score(y_test, ae_scores) if len(np.unique(y_test)) > 1 else 0.0

        metrics["autoencoder"] = {
            "classification_report": ae_report,
            "roc_auc": float(ae_auc),
            "pr_auc": float(ae_pr),
            "confusion_matrix": confusion_matrix(y_test, ae_pred).tolist(),
        }

        # LSTM (sequence-level)
        logger.info("Evaluating LSTM...")
        lstm_pred, lstm_prob = self.lstm_model.predict(X_test)

        # Align labels to sequence windows (max over each window as in training)
        L = self.lstm_model.sequence_length
        y_seq = np.array([y_test[i:i+L].max() for i in range(len(y_test) - L + 1)], dtype=int)

        lstm_report = classification_report(
            y_seq, lstm_pred, output_dict=True, zero_division=0
        )
        lstm_auc = roc_auc_score(y_seq, lstm_prob) if len(np.unique(y_seq)) > 1 else 0.0
        lstm_pr = average_precision_score(y_seq, lstm_prob) if len(np.unique(y_seq)) > 1 else 0.0

        metrics["lstm"] = {
            "classification_report": lstm_report,
            "roc_auc": float(lstm_auc),
            "pr_auc": float(lstm_pr),
            "confusion_matrix": confusion_matrix(y_seq, lstm_pred).tolist(),
        }

        logger.info("Autoencoder AUC: %.4f | PR-AUC: %.4f", ae_auc, ae_pr)
        logger.info("LSTM        AUC: %.4f | PR-AUC: %.4f", lstm_auc, lstm_pr)

        return metrics

    def save_models(self):
        """Save trained models and preprocessor."""
        model_dir = self.settings.ml.model_path
        os.makedirs(model_dir, exist_ok=True)

        # Preprocessor
        preproc_path = os.path.join(model_dir, "preprocessor.joblib")
        self.preprocessor.save(preproc_path)

        # Autoencoder
        ae_model_path = os.path.join(model_dir, "autoencoder.keras")
        ae_meta_path = ae_model_path + ".meta.pkl"
        self.autoencoder.save(ae_model_path, meta_path=ae_meta_path)

        # LSTM
        lstm_path = os.path.join(model_dir, "lstm_model.keras")
        self.lstm_model.save(lstm_path)

        # Metrics
        metrics_path = os.path.join(model_dir, "metrics.joblib")
        joblib.dump(self.metrics, metrics_path)

        logger.info("All models saved to %s", model_dir)

    def load_models(self) -> bool:
        """Load pre-trained models."""
        model_dir = self.settings.ml.model_path
        try:
            # Preprocessor
            preproc_path = os.path.join(model_dir, "preprocessor.joblib")
            self.preprocessor = TransactionPreprocessor()
            self.preprocessor.load(preproc_path)

            # Autoencoder
            ae_model_path = os.path.join(model_dir, "autoencoder.keras")
            ae_meta_path = ae_model_path + ".meta.pkl"
            self.autoencoder = FraudAutoencoder(input_dim=len(self.preprocessor.feature_names_))
            self.autoencoder.load(ae_model_path, meta_path=ae_meta_path)

            # LSTM
            lstm_path = os.path.join(model_dir, "lstm_model.keras")
            self.lstm_model = FraudLSTM(input_dim=len(self.preprocessor.feature_names_))
            self.lstm_model.load(lstm_path)

            # Metrics
            metrics_path = os.path.join(model_dir, "metrics.joblib")
            if os.path.exists(metrics_path):
                self.metrics = joblib.load(metrics_path)

            logger.info("All models loaded successfully.")
            return True
        except Exception as e:
            logger.error("Error loading models: %s", e)
            return False
