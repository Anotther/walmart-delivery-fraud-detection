"""
Risk scoring system for fraud detection.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.models.outlier_detection import IsolationForestModel, EnsembleOutlierDetector
from src.models.clustering import KMeansModel


@dataclass
class RiskScore:
    """Represents a risk score for an entity."""
    entity_type: str  # 'order', 'driver', 'customer'
    entity_id: str
    score: float  # 0-100
    category: str  # 'Low', 'Medium', 'High', 'Critical'
    factors: Dict[str, float]  # Contributing factors


class RiskScoringEngine:
    """Engine for calculating comprehensive risk scores."""

    # Risk category thresholds
    RISK_THRESHOLDS = {
        "low": 25,
        "medium": 50,
        "high": 75,
    }

    # Feature weights for scoring
    DEFAULT_WEIGHTS = {
        "missing_rate": 0.25,
        "historical_pattern": 0.20,
        "anomaly_score": 0.25,
        "cluster_risk": 0.15,
        "frequency": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the scoring engine.

        Args:
            weights: Custom weights for score components
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.outlier_model = None
        self.cluster_model = None
        self.is_fitted = False

    def fit(self, X: pd.DataFrame) -> "RiskScoringEngine":
        """
        Fit the underlying models.

        Args:
            X: Feature DataFrame

        Returns:
            Self
        """
        self.outlier_model = EnsembleOutlierDetector()
        self.outlier_model.fit(X)

        self.cluster_model = KMeansModel(n_clusters=5)
        self.cluster_model.fit(X)

        self.is_fitted = True
        return self

    def _categorize_risk(self, score: float) -> str:
        """Convert numeric score to category."""
        if score < self.RISK_THRESHOLDS["low"]:
            return "Low"
        elif score < self.RISK_THRESHOLDS["medium"]:
            return "Medium"
        elif score < self.RISK_THRESHOLDS["high"]:
            return "High"
        return "Critical"

    def _normalize(self, values: np.ndarray) -> np.ndarray:
        """Normalize values to 0-100 scale."""
        min_val = values.min()
        max_val = values.max()
        if max_val - min_val == 0:
            return np.full(len(values), 50.0)
        return (values - min_val) / (max_val - min_val) * 100

    def score_orders(
        self,
        orders_df: pd.DataFrame,
        feature_df: pd.DataFrame
    ) -> List[RiskScore]:
        """
        Calculate risk scores for orders.

        Args:
            orders_df: Orders DataFrame with order_id
            feature_df: Feature DataFrame for scoring

        Returns:
            List of RiskScore objects
        """
        if not self.is_fitted:
            raise ValueError("Engine not fitted. Call fit() first.")

        scores = []

        # Get model scores
        anomaly_scores = 1 - self.outlier_model.score(feature_df)  # Invert so higher = riskier
        anomaly_scores_norm = self._normalize(anomaly_scores)

        cluster_labels = self.cluster_model.predict(feature_df)
        cluster_distances = self.cluster_model.score(feature_df)
        cluster_scores_norm = self._normalize(cluster_distances)

        # Calculate missing rate component
        if "items_missing" in orders_df.columns and "items_delivered" in orders_df.columns:
            total_items = orders_df["items_delivered"] + orders_df["items_missing"]
            missing_rate = np.where(
                total_items > 0,
                orders_df["items_missing"] / total_items * 100,
                0
            )
            missing_scores = self._normalize(missing_rate)
        else:
            missing_scores = np.zeros(len(orders_df))

        # Calculate final scores
        for i, row in orders_df.iterrows():
            idx = orders_df.index.get_loc(i)

            factors = {
                "missing_rate": missing_scores[idx],
                "anomaly_score": anomaly_scores_norm[idx],
                "cluster_distance": cluster_scores_norm[idx],
            }

            final_score = (
                factors["missing_rate"] * self.weights["missing_rate"] +
                factors["anomaly_score"] * self.weights["anomaly_score"] +
                factors["cluster_distance"] * self.weights["cluster_risk"]
            )

            # Normalize to account for used weights
            used_weight = (
                self.weights["missing_rate"] +
                self.weights["anomaly_score"] +
                self.weights["cluster_risk"]
            )
            final_score = final_score / used_weight * 100

            scores.append(RiskScore(
                entity_type="order",
                entity_id=str(row.get("order_id", i)),
                score=min(final_score, 100),
                category=self._categorize_risk(final_score),
                factors=factors
            ))

        return scores

    def score_drivers(
        self,
        driver_features: pd.DataFrame
    ) -> List[RiskScore]:
        """
        Calculate risk scores for drivers.

        Args:
            driver_features: Driver features DataFrame

        Returns:
            List of RiskScore objects
        """
        scores = []

        # Normalize key metrics
        if "missing_rate" in driver_features.columns:
            missing_scores = self._normalize(driver_features["missing_rate"].values)
        else:
            missing_scores = np.zeros(len(driver_features))

        if "pct_orders_with_missing" in driver_features.columns:
            pct_scores = self._normalize(driver_features["pct_orders_with_missing"].values)
        else:
            pct_scores = np.zeros(len(driver_features))

        if "total_items_missing" in driver_features.columns:
            volume_scores = self._normalize(driver_features["total_items_missing"].values)
        else:
            volume_scores = np.zeros(len(driver_features))

        for i, row in driver_features.iterrows():
            idx = driver_features.index.get_loc(i)

            factors = {
                "missing_rate": missing_scores[idx],
                "pct_orders_with_issues": pct_scores[idx],
                "volume_missing": volume_scores[idx],
            }

            final_score = (
                factors["missing_rate"] * 0.4 +
                factors["pct_orders_with_issues"] * 0.35 +
                factors["volume_missing"] * 0.25
            )

            scores.append(RiskScore(
                entity_type="driver",
                entity_id=str(row.get("driver_id", i)),
                score=min(final_score, 100),
                category=self._categorize_risk(final_score),
                factors=factors
            ))

        return scores

    def score_customers(
        self,
        customer_features: pd.DataFrame
    ) -> List[RiskScore]:
        """
        Calculate risk scores for customers.

        Args:
            customer_features: Customer features DataFrame

        Returns:
            List of RiskScore objects
        """
        scores = []

        # Normalize key metrics
        if "missing_rate" in customer_features.columns:
            missing_scores = self._normalize(customer_features["missing_rate"].values)
        else:
            missing_scores = np.zeros(len(customer_features))

        if "pct_orders_with_missing" in customer_features.columns:
            pct_scores = self._normalize(customer_features["pct_orders_with_missing"].values)
        else:
            pct_scores = np.zeros(len(customer_features))

        if "orders_with_missing" in customer_features.columns:
            freq_scores = self._normalize(customer_features["orders_with_missing"].values)
        else:
            freq_scores = np.zeros(len(customer_features))

        for i, row in customer_features.iterrows():
            idx = customer_features.index.get_loc(i)

            factors = {
                "missing_rate": missing_scores[idx],
                "pct_orders_with_issues": pct_scores[idx],
                "issue_frequency": freq_scores[idx],
            }

            final_score = (
                factors["missing_rate"] * 0.4 +
                factors["pct_orders_with_issues"] * 0.35 +
                factors["issue_frequency"] * 0.25
            )

            scores.append(RiskScore(
                entity_type="customer",
                entity_id=str(row.get("customer_id", i)),
                score=min(final_score, 100),
                category=self._categorize_risk(final_score),
                factors=factors
            ))

        return scores


def create_risk_report(scores: List[RiskScore]) -> pd.DataFrame:
    """
    Create a DataFrame report from risk scores.

    Args:
        scores: List of RiskScore objects

    Returns:
        DataFrame with risk report
    """
    records = []
    for score in scores:
        record = {
            "entity_type": score.entity_type,
            "entity_id": score.entity_id,
            "risk_score": score.score,
            "risk_category": score.category,
        }
        record.update({f"factor_{k}": v for k, v in score.factors.items()})
        records.append(record)

    df = pd.DataFrame(records)
    return df.sort_values("risk_score", ascending=False)


def get_high_risk_entities(
    scores: List[RiskScore],
    threshold: float = 75.0
) -> List[RiskScore]:
    """
    Filter high-risk entities.

    Args:
        scores: List of RiskScore objects
        threshold: Minimum score to be considered high-risk

    Returns:
        Filtered list of high-risk entities
    """
    return [s for s in scores if s.score >= threshold]
