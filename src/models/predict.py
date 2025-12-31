"""
Prediction pipeline for fraud detection.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import OUTPUT_DIR
from src.models.outlier_detection import IsolationForestModel, EnsembleOutlierDetector
from src.models.clustering import KMeansModel
from src.models.risk_scoring import RiskScoringEngine, RiskScore, create_risk_report


class FraudPredictor:
    """Unified fraud prediction interface."""

    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize the predictor.

        Args:
            model_dir: Directory containing saved models
        """
        self.model_dir = model_dir or OUTPUT_DIR / "models"
        self.models = {}
        self.is_loaded = False

    def load_models(self) -> "FraudPredictor":
        """
        Load all trained models.

        Returns:
            Self
        """
        model_files = {
            "isolation_forest": "isolation_forest.joblib",
            "kmeans": "kmeans.joblib",
            "ensemble": "ensemble_outlier.joblib",
        }

        for name, filename in model_files.items():
            path = self.model_dir / filename
            if path.exists():
                if name == "isolation_forest":
                    self.models[name] = IsolationForestModel.load(path)
                elif name == "kmeans":
                    self.models[name] = KMeansModel.load(path)
                elif name == "ensemble":
                    self.models[name] = EnsembleOutlierDetector.load(path)
                print(f"Loaded {name} from {path}")
            else:
                print(f"Warning: {name} model not found at {path}")

        self.is_loaded = len(self.models) > 0
        return self

    def predict_anomalies(
        self,
        X: pd.DataFrame,
        method: str = "ensemble"
    ) -> np.ndarray:
        """
        Predict anomalies using specified method.

        Args:
            X: Feature DataFrame
            method: 'isolation_forest', 'ensemble', or 'voting'

        Returns:
            Array of predictions (1 for normal, -1 for anomaly)
        """
        if not self.is_loaded:
            raise ValueError("Models not loaded. Call load_models() first.")

        if method == "isolation_forest" and "isolation_forest" in self.models:
            return self.models["isolation_forest"].predict(X)
        elif method == "ensemble" and "ensemble" in self.models:
            return self.models["ensemble"].predict(X)
        elif method == "voting":
            # Use all available models
            predictions = []
            for model in self.models.values():
                if hasattr(model, "predict"):
                    try:
                        pred = model.predict(X)
                        if len(pred) == len(X):
                            predictions.append(pred)
                    except Exception:
                        continue

            if not predictions:
                raise ValueError("No valid predictions from models")

            # Majority vote
            votes = np.array(predictions).sum(axis=0)
            return np.where(votes < 0, -1, 1)
        else:
            raise ValueError(f"Unknown method: {method}")

    def get_anomaly_scores(
        self,
        X: pd.DataFrame,
        method: str = "ensemble"
    ) -> np.ndarray:
        """
        Get anomaly scores.

        Args:
            X: Feature DataFrame
            method: Scoring method

        Returns:
            Array of anomaly scores
        """
        if not self.is_loaded:
            raise ValueError("Models not loaded. Call load_models() first.")

        if method == "isolation_forest" and "isolation_forest" in self.models:
            return self.models["isolation_forest"].get_risk_scores(X)
        elif method == "ensemble" and "ensemble" in self.models:
            scores = self.models["ensemble"].score(X)
            # Normalize to 0-100 (invert so higher = more anomalous)
            return (1 - scores) * 100
        else:
            raise ValueError(f"Unknown method or model not loaded: {method}")

    def get_clusters(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get cluster assignments.

        Args:
            X: Feature DataFrame

        Returns:
            Array of cluster labels
        """
        if "kmeans" not in self.models:
            raise ValueError("K-Means model not loaded")

        return self.models["kmeans"].predict(X)

    def predict_with_details(
        self,
        X: pd.DataFrame,
        original_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Get comprehensive predictions with all available information.

        Args:
            X: Feature DataFrame
            original_df: Original data for additional context

        Returns:
            DataFrame with predictions and scores
        """
        if not self.is_loaded:
            raise ValueError("Models not loaded. Call load_models() first.")

        result = original_df.copy() if original_df is not None else X.copy()

        # Anomaly predictions
        if "ensemble" in self.models:
            result["is_anomaly"] = self.models["ensemble"].predict(X) == -1
            result["anomaly_score"] = self.get_anomaly_scores(X, method="ensemble")
        elif "isolation_forest" in self.models:
            result["is_anomaly"] = self.models["isolation_forest"].predict(X) == -1
            result["anomaly_score"] = self.get_anomaly_scores(X, method="isolation_forest")

        # Cluster assignments
        if "kmeans" in self.models:
            result["cluster"] = self.models["kmeans"].predict(X)
            result["cluster_distance"] = self.models["kmeans"].score(X)

        # Risk category based on anomaly score
        if "anomaly_score" in result.columns:
            result["risk_category"] = pd.cut(
                result["anomaly_score"],
                bins=[-1, 25, 50, 75, 100],
                labels=["Low", "Medium", "High", "Critical"]
            )

        return result


def predict_order_fraud(
    orders_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    model_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Predict fraud for orders.

    Args:
        orders_df: Orders DataFrame
        feature_df: Feature DataFrame
        model_dir: Model directory

    Returns:
        DataFrame with fraud predictions
    """
    predictor = FraudPredictor(model_dir)
    predictor.load_models()

    return predictor.predict_with_details(feature_df, orders_df)


def predict_driver_risk(
    driver_features: pd.DataFrame,
    model_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Predict risk scores for drivers.

    Args:
        driver_features: Driver features DataFrame
        model_dir: Model directory

    Returns:
        DataFrame with risk scores
    """
    # Use rule-based scoring for drivers
    df = driver_features.copy()

    # Normalize metrics
    def normalize(series):
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series([50.0] * len(series))
        return (series - min_val) / (max_val - min_val) * 100

    if "missing_rate" in df.columns:
        df["missing_rate_score"] = normalize(df["missing_rate"])
    else:
        df["missing_rate_score"] = 0

    if "pct_orders_with_missing" in df.columns:
        df["pct_orders_score"] = normalize(df["pct_orders_with_missing"])
    else:
        df["pct_orders_score"] = 0

    # Calculate overall risk score
    df["risk_score"] = (
        df["missing_rate_score"] * 0.5 +
        df["pct_orders_score"] * 0.5
    )

    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"]
    )

    return df


def predict_customer_risk(
    customer_features: pd.DataFrame,
    model_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Predict risk scores for customers.

    Args:
        customer_features: Customer features DataFrame
        model_dir: Model directory

    Returns:
        DataFrame with risk scores
    """
    df = customer_features.copy()

    # Normalize metrics
    def normalize(series):
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series([50.0] * len(series))
        return (series - min_val) / (max_val - min_val) * 100

    if "missing_rate" in df.columns:
        df["missing_rate_score"] = normalize(df["missing_rate"])
    else:
        df["missing_rate_score"] = 0

    if "pct_orders_with_missing" in df.columns:
        df["pct_orders_score"] = normalize(df["pct_orders_with_missing"])
    else:
        df["pct_orders_score"] = 0

    # Calculate overall risk score
    df["risk_score"] = (
        df["missing_rate_score"] * 0.5 +
        df["pct_orders_score"] * 0.5
    )

    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"]
    )

    return df


if __name__ == "__main__":
    # Test prediction pipeline
    from src.etl.extractors import extract_all
    from src.etl.transformers import transform_all
    from src.features.aggregations import create_fraud_detection_dataset

    print("Loading data...")
    raw_data = extract_all()
    data = transform_all(raw_data)

    print("Creating features...")
    ml_data = create_fraud_detection_dataset(
        data["orders"],
        data["drivers"],
        data["customers"]
    )

    # Get feature columns
    feature_cols = [
        "order_amount", "items_delivered", "items_missing",
        "driver_missing_rate", "customer_missing_rate"
    ]
    available_cols = [col for col in feature_cols if col in ml_data.columns]
    X = ml_data[available_cols].fillna(0)

    print("\nRunning predictions...")
    predictor = FraudPredictor()
    predictor.load_models()

    if predictor.is_loaded:
        results = predictor.predict_with_details(X, ml_data)
        print(f"\nPredictions complete for {len(results)} orders")
        print(f"Anomalies detected: {results['is_anomaly'].sum()}")
        print(f"\nRisk category distribution:")
        print(results["risk_category"].value_counts())
    else:
        print("No trained models found. Run train.py first.")
