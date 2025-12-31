"""
Base classes and utilities for ML models.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

from src.config.settings import OUTPUT_DIR


class BaseFraudModel(ABC):
    """Abstract base class for fraud detection models."""

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the model.

        Args:
            name: Model name for identification
            params: Model parameters
        """
        self.name = name
        self.params = params or {}
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "BaseFraudModel":
        """Fit the model to data."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions on new data."""
        pass

    @abstractmethod
    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Get anomaly/risk scores for data."""
        pass

    def preprocess(self, X: pd.DataFrame, fit: bool = False) -> np.ndarray:
        """
        Preprocess data for modeling.

        Args:
            X: Input DataFrame
            fit: Whether to fit the scaler

        Returns:
            Scaled numpy array
        """
        # Store feature names
        if fit:
            self.feature_names = list(X.columns)

        # Handle missing values
        X_clean = X.fillna(X.median())

        # Convert boolean columns
        for col in X_clean.columns:
            if X_clean[col].dtype == bool:
                X_clean[col] = X_clean[col].astype(int)

        # Scale
        if fit:
            return self.scaler.fit_transform(X_clean)
        return self.scaler.transform(X_clean)

    def save(self, path: Optional[Path] = None) -> Path:
        """
        Save model to disk.

        Args:
            path: Custom save path

        Returns:
            Path where model was saved
        """
        if path is None:
            path = OUTPUT_DIR / "models" / f"{self.name}.joblib"

        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "name": self.name,
            "params": self.params,
            "model": self.model,
            "scaler": self.scaler,
            "is_fitted": self.is_fitted,
            "feature_names": self.feature_names,
        }

        joblib.dump(model_data, path)
        return path

    @classmethod
    def load(cls, path: Path) -> "BaseFraudModel":
        """
        Load model from disk.

        Args:
            path: Path to saved model

        Returns:
            Loaded model instance
        """
        model_data = joblib.load(path)

        instance = cls(
            name=model_data["name"],
            params=model_data["params"]
        )
        instance.model = model_data["model"]
        instance.scaler = model_data["scaler"]
        instance.is_fitted = model_data["is_fitted"]
        instance.feature_names = model_data["feature_names"]

        return instance

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance if available.

        Returns:
            Dictionary of feature names to importance scores
        """
        return None


def prepare_features(
    orders_df: pd.DataFrame,
    driver_features: pd.DataFrame,
    customer_features: pd.DataFrame
) -> Tuple[pd.DataFrame, list]:
    """
    Prepare features for fraud detection model.

    Args:
        orders_df: Orders DataFrame
        driver_features: Driver features DataFrame
        customer_features: Customer features DataFrame

    Returns:
        Tuple of (feature DataFrame, feature column names)
    """
    # Select driver features to join
    driver_cols = ["driver_id", "missing_rate", "total_orders", "pct_orders_with_missing", "age"]
    driver_subset = driver_features[driver_cols].rename(columns={
        "missing_rate": "driver_missing_rate",
        "total_orders": "driver_total_orders",
        "pct_orders_with_missing": "driver_pct_with_missing",
        "age": "driver_age"
    })

    # Select customer features to join
    customer_cols = ["customer_id", "missing_rate", "total_orders", "customer_age"]
    customer_subset = customer_features[customer_cols].rename(columns={
        "missing_rate": "customer_missing_rate",
        "total_orders": "customer_total_orders"
    })

    # Merge
    df = orders_df.merge(driver_subset, on="driver_id", how="left")
    df = df.merge(customer_subset, on="customer_id", how="left")

    # Select numeric features
    feature_cols = [
        "order_amount", "items_delivered", "items_missing",
        "driver_missing_rate", "driver_total_orders", "driver_pct_with_missing", "driver_age",
        "customer_missing_rate", "customer_total_orders", "customer_age"
    ]

    # Filter to available columns
    available_cols = [col for col in feature_cols if col in df.columns]

    return df[available_cols], available_cols
