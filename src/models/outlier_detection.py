"""
Outlier detection models for fraud detection.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from src.models.base import BaseFraudModel


class IsolationForestModel(BaseFraudModel):
    """Isolation Forest for anomaly detection."""

    def __init__(
        self,
        name: str = "isolation_forest",
        contamination: float = 0.1,
        n_estimators: int = 100,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Isolation Forest model.

        Args:
            name: Model name
            contamination: Expected proportion of outliers
            n_estimators: Number of trees
            params: Additional parameters
        """
        default_params = {
            "contamination": contamination,
            "n_estimators": n_estimators,
            "random_state": 42,
            "n_jobs": -1,
        }
        if params:
            default_params.update(params)

        super().__init__(name, default_params)

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "IsolationForestModel":
        """
        Fit the Isolation Forest model.

        Args:
            X: Feature DataFrame
            y: Not used (unsupervised)

        Returns:
            Self
        """
        X_scaled = self.preprocess(X, fit=True)

        self.model = IsolationForest(**self.params)
        self.model.fit(X_scaled)
        self.is_fitted = True

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predictions (1 for normal, -1 for anomaly)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        return self.model.predict(X_scaled)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly scores.

        Args:
            X: Feature DataFrame

        Returns:
            Array of anomaly scores (lower = more anomalous)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        return self.model.score_samples(X_scaled)

    def get_risk_scores(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get normalized risk scores (0-100, higher = more risk).

        Args:
            X: Feature DataFrame

        Returns:
            Array of risk scores
        """
        raw_scores = self.score(X)

        # Normalize to 0-100 (invert because lower score = more anomalous)
        min_score = raw_scores.min()
        max_score = raw_scores.max()

        if max_score - min_score == 0:
            return np.full(len(raw_scores), 50.0)

        normalized = (max_score - raw_scores) / (max_score - min_score) * 100
        return normalized


class LOFModel(BaseFraudModel):
    """Local Outlier Factor for anomaly detection."""

    def __init__(
        self,
        name: str = "lof",
        n_neighbors: int = 20,
        contamination: float = 0.1,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LOF model.

        Args:
            name: Model name
            n_neighbors: Number of neighbors
            contamination: Expected proportion of outliers
            params: Additional parameters
        """
        default_params = {
            "n_neighbors": n_neighbors,
            "contamination": contamination,
            "novelty": True,  # Enable predict on new data
            "n_jobs": -1,
        }
        if params:
            default_params.update(params)

        super().__init__(name, default_params)

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "LOFModel":
        """
        Fit the LOF model.

        Args:
            X: Feature DataFrame
            y: Not used (unsupervised)

        Returns:
            Self
        """
        X_scaled = self.preprocess(X, fit=True)

        self.model = LocalOutlierFactor(**self.params)
        self.model.fit(X_scaled)
        self.is_fitted = True

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predictions (1 for normal, -1 for anomaly)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        return self.model.predict(X_scaled)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly scores.

        Args:
            X: Feature DataFrame

        Returns:
            Array of anomaly scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        return self.model.score_samples(X_scaled)


class EnsembleOutlierDetector(BaseFraudModel):
    """Ensemble of outlier detection methods."""

    def __init__(
        self,
        name: str = "ensemble_outlier",
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ensemble model.

        Args:
            name: Model name
            params: Parameters for sub-models
        """
        super().__init__(name, params or {})

        self.models = {
            "isolation_forest": IsolationForestModel(
                contamination=params.get("contamination", 0.1) if params else 0.1
            ),
            "lof": LOFModel(
                contamination=params.get("contamination", 0.1) if params else 0.1
            ),
        }

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "EnsembleOutlierDetector":
        """
        Fit all models in the ensemble.

        Args:
            X: Feature DataFrame
            y: Not used

        Returns:
            Self
        """
        for model in self.models.values():
            model.fit(X)

        self.is_fitted = True
        self.feature_names = list(X.columns)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using voting ensemble.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predictions (-1 if majority vote anomaly)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        predictions = np.array([model.predict(X) for model in self.models.values()])

        # Majority vote (sum < 0 means majority voted -1)
        votes = predictions.sum(axis=0)
        return np.where(votes < 0, -1, 1)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get average anomaly score from all models.

        Args:
            X: Feature DataFrame

        Returns:
            Array of averaged scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        scores = []
        for name, model in self.models.items():
            model_scores = model.score(X)
            # Normalize each model's scores
            min_s, max_s = model_scores.min(), model_scores.max()
            if max_s - min_s > 0:
                normalized = (model_scores - min_s) / (max_s - min_s)
            else:
                normalized = np.full(len(model_scores), 0.5)
            scores.append(normalized)

        return np.mean(scores, axis=0)

    def get_model_predictions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get predictions from each model separately.

        Args:
            X: Feature DataFrame

        Returns:
            Dictionary of model name to predictions
        """
        return {name: model.predict(X) for name, model in self.models.items()}
