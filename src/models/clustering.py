"""
Clustering models for fraud pattern discovery.
"""
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score

from src.models.base import BaseFraudModel


class KMeansModel(BaseFraudModel):
    """K-Means clustering for fraud pattern discovery."""

    def __init__(
        self,
        name: str = "kmeans",
        n_clusters: int = 5,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize K-Means model.

        Args:
            name: Model name
            n_clusters: Number of clusters
            params: Additional parameters
        """
        default_params = {
            "n_clusters": n_clusters,
            "random_state": 42,
            "n_init": 10,
        }
        if params:
            default_params.update(params)

        super().__init__(name, default_params)

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "KMeansModel":
        """
        Fit the K-Means model.

        Args:
            X: Feature DataFrame
            y: Not used

        Returns:
            Self
        """
        X_scaled = self.preprocess(X, fit=True)

        self.model = KMeans(**self.params)
        self.model.fit(X_scaled)
        self.is_fitted = True

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict cluster assignments.

        Args:
            X: Feature DataFrame

        Returns:
            Array of cluster labels
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        return self.model.predict(X_scaled)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get distance to cluster center (anomaly score).

        Args:
            X: Feature DataFrame

        Returns:
            Array of distances to assigned cluster center
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        labels = self.model.predict(X_scaled)
        centers = self.model.cluster_centers_

        # Calculate distance to assigned cluster center
        distances = np.array([
            np.linalg.norm(X_scaled[i] - centers[labels[i]])
            for i in range(len(X_scaled))
        ])

        return distances

    def get_silhouette_score(self, X: pd.DataFrame) -> float:
        """
        Calculate silhouette score.

        Args:
            X: Feature DataFrame

        Returns:
            Silhouette score
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_scaled = self.preprocess(X)
        labels = self.model.predict(X_scaled)

        return silhouette_score(X_scaled, labels)

    def get_cluster_statistics(self, X: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get statistics for each cluster.

        Args:
            X: Feature DataFrame
            original_df: Original data with all columns

        Returns:
            DataFrame with cluster statistics
        """
        labels = self.predict(X)
        original_df = original_df.copy()
        original_df["cluster"] = labels

        stats = original_df.groupby("cluster").agg({
            "order_id": "count" if "order_id" in original_df.columns else "size",
        })

        # Add numeric column means
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in original_df.columns:
                stats[f"avg_{col}"] = original_df.groupby("cluster")[col].mean()

        return stats

    @staticmethod
    def find_optimal_k(X: pd.DataFrame, k_range: range = range(2, 11)) -> Tuple[int, List[float]]:
        """
        Find optimal number of clusters using silhouette score.

        Args:
            X: Feature DataFrame
            k_range: Range of k values to try

        Returns:
            Tuple of (optimal k, list of silhouette scores)
        """
        scaler = KMeansModel(n_clusters=2)
        X_scaled = scaler.preprocess(X, fit=True)

        silhouettes = []
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            silhouettes.append(score)

        optimal_k = k_range[np.argmax(silhouettes)]
        return optimal_k, silhouettes


class DBSCANModel(BaseFraudModel):
    """DBSCAN clustering for anomaly detection."""

    def __init__(
        self,
        name: str = "dbscan",
        eps: float = 0.5,
        min_samples: int = 10,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize DBSCAN model.

        Args:
            name: Model name
            eps: Maximum distance between samples
            min_samples: Minimum samples in neighborhood
            params: Additional parameters
        """
        default_params = {
            "eps": eps,
            "min_samples": min_samples,
            "n_jobs": -1,
        }
        if params:
            default_params.update(params)

        super().__init__(name, default_params)
        self._labels = None

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "DBSCANModel":
        """
        Fit the DBSCAN model.

        Args:
            X: Feature DataFrame
            y: Not used

        Returns:
            Self
        """
        X_scaled = self.preprocess(X, fit=True)

        self.model = DBSCAN(**self.params)
        self._labels = self.model.fit_predict(X_scaled)
        self.is_fitted = True

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get cluster labels (note: DBSCAN doesn't predict on new data).

        For new data, returns -1 (noise) for points not fitting existing clusters.

        Args:
            X: Feature DataFrame

        Returns:
            Array of cluster labels (-1 for noise/anomaly)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # DBSCAN doesn't have predict for new data
        # Return stored labels if same data, otherwise mark as noise
        if len(X) == len(self._labels):
            return self._labels

        # For new data, we need to refit (limitation of DBSCAN)
        X_scaled = self.preprocess(X)
        dbscan = DBSCAN(**self.params)
        return dbscan.fit_predict(X_scaled)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly scores (binary: noise or not).

        Args:
            X: Feature DataFrame

        Returns:
            Array of scores (1 for noise/anomaly, 0 for normal)
        """
        labels = self.predict(X)
        return (labels == -1).astype(float)

    def get_noise_points(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get indices of noise points (potential anomalies).

        Args:
            X: Feature DataFrame

        Returns:
            Array of indices
        """
        labels = self.predict(X)
        return np.where(labels == -1)[0]

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about discovered clusters.

        Returns:
            Dictionary with cluster info
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        unique_labels = set(self._labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = (self._labels == -1).sum()

        return {
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "noise_ratio": n_noise / len(self._labels),
            "labels": unique_labels,
        }


class FraudClusterAnalyzer:
    """Combines clustering methods for comprehensive fraud analysis."""

    def __init__(self):
        """Initialize the analyzer."""
        self.kmeans = None
        self.dbscan = None
        self.is_fitted = False

    def fit(
        self,
        X: pd.DataFrame,
        n_clusters: Optional[int] = None,
        eps: float = 0.5,
        min_samples: int = 10
    ) -> "FraudClusterAnalyzer":
        """
        Fit both clustering models.

        Args:
            X: Feature DataFrame
            n_clusters: Number of clusters for K-Means (auto if None)
            eps: DBSCAN eps parameter
            min_samples: DBSCAN min_samples

        Returns:
            Self
        """
        # Find optimal k if not specified
        if n_clusters is None:
            n_clusters, _ = KMeansModel.find_optimal_k(X)

        self.kmeans = KMeansModel(n_clusters=n_clusters)
        self.kmeans.fit(X)

        self.dbscan = DBSCANModel(eps=eps, min_samples=min_samples)
        self.dbscan.fit(X)

        self.is_fitted = True
        return self

    def analyze(self, X: pd.DataFrame, original_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive cluster analysis.

        Args:
            X: Feature DataFrame
            original_df: Original data

        Returns:
            Dictionary with analysis results
        """
        if not self.is_fitted:
            raise ValueError("Analyzer not fitted. Call fit() first.")

        results = {
            "kmeans": {
                "labels": self.kmeans.predict(X),
                "silhouette": self.kmeans.get_silhouette_score(X),
                "cluster_stats": self.kmeans.get_cluster_statistics(X, original_df),
            },
            "dbscan": {
                "labels": self.dbscan.predict(X),
                "info": self.dbscan.get_cluster_info(),
                "noise_indices": self.dbscan.get_noise_points(X),
            },
        }

        # Find high-risk cluster (highest average missing rate)
        if "missing_rate" in original_df.columns or "items_missing" in original_df.columns:
            df_with_clusters = original_df.copy()
            df_with_clusters["kmeans_cluster"] = results["kmeans"]["labels"]

            metric = "missing_rate" if "missing_rate" in df_with_clusters.columns else "items_missing"
            cluster_risk = df_with_clusters.groupby("kmeans_cluster")[metric].mean()
            results["high_risk_cluster"] = cluster_risk.idxmax()
            results["high_risk_cluster_rate"] = cluster_risk.max()

        return results
