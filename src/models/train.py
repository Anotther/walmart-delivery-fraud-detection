"""
Model training pipeline.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import mlflow
import mlflow.sklearn

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME, OUTPUT_DIR
from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.driver_features import create_driver_features
from src.features.customer_features import create_customer_features
from src.features.aggregations import create_fraud_detection_dataset
from src.models.outlier_detection import IsolationForestModel, LOFModel, EnsembleOutlierDetector
from src.models.clustering import KMeansModel, DBSCANModel
from src.models.risk_scoring import RiskScoringEngine


def setup_mlflow():
    """Setup MLflow tracking."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)


def prepare_training_data() -> Dict[str, pd.DataFrame]:
    """
    Prepare data for model training.

    Returns:
        Dictionary with all necessary DataFrames
    """
    print("Loading and transforming data...")
    raw_data = extract_all()
    data = transform_all(raw_data)

    orders = data["orders"]
    drivers = data["drivers"]
    customers = data["customers"]

    print("Creating features...")
    driver_features = create_driver_features(drivers, orders)
    customer_features = create_customer_features(customers, orders)
    ml_dataset = create_fraud_detection_dataset(orders, drivers, customers)

    return {
        "orders": orders,
        "drivers": drivers,
        "customers": customers,
        "driver_features": driver_features,
        "customer_features": customer_features,
        "ml_dataset": ml_dataset,
    }


def get_feature_columns(df: pd.DataFrame) -> list:
    """Get numeric feature columns for modeling."""
    feature_cols = [
        "order_amount", "items_delivered", "items_missing", "total_items",
        "missing_rate", "is_high_value", "is_weekend",
        "driver_age", "trips", "driver_missing_rate", "driver_total_orders",
        "customer_age", "customer_missing_rate", "customer_total_orders"
    ]
    return [col for col in feature_cols if col in df.columns]


def train_isolation_forest(
    X: pd.DataFrame,
    contamination: float = 0.1
) -> IsolationForestModel:
    """
    Train Isolation Forest model.

    Args:
        X: Feature DataFrame
        contamination: Expected proportion of outliers

    Returns:
        Trained model
    """
    with mlflow.start_run(run_name="isolation_forest"):
        mlflow.log_params({
            "model_type": "IsolationForest",
            "contamination": contamination,
            "n_features": len(X.columns),
        })

        model = IsolationForestModel(contamination=contamination)
        model.fit(X)

        predictions = model.predict(X)
        n_anomalies = (predictions == -1).sum()

        mlflow.log_metrics({
            "n_anomalies": n_anomalies,
            "anomaly_rate": n_anomalies / len(X) * 100,
        })

        # Save model
        model_path = model.save()
        mlflow.log_artifact(str(model_path))

        print(f"Isolation Forest: {n_anomalies} anomalies detected ({n_anomalies/len(X)*100:.2f}%)")

    return model


def train_kmeans(
    X: pd.DataFrame,
    n_clusters: Optional[int] = None
) -> KMeansModel:
    """
    Train K-Means model.

    Args:
        X: Feature DataFrame
        n_clusters: Number of clusters (auto-detect if None)

    Returns:
        Trained model
    """
    with mlflow.start_run(run_name="kmeans"):
        # Find optimal k if not specified
        if n_clusters is None:
            n_clusters, silhouettes = KMeansModel.find_optimal_k(X)
            print(f"Optimal k: {n_clusters}")

        mlflow.log_params({
            "model_type": "KMeans",
            "n_clusters": n_clusters,
            "n_features": len(X.columns),
        })

        model = KMeansModel(n_clusters=n_clusters)
        model.fit(X)

        silhouette = model.get_silhouette_score(X)

        mlflow.log_metrics({
            "silhouette_score": silhouette,
            "inertia": model.model.inertia_,
        })

        model_path = model.save()
        mlflow.log_artifact(str(model_path))

        print(f"K-Means: silhouette score = {silhouette:.4f}")

    return model


def train_ensemble(X: pd.DataFrame) -> EnsembleOutlierDetector:
    """
    Train ensemble outlier detector.

    Args:
        X: Feature DataFrame

    Returns:
        Trained ensemble model
    """
    with mlflow.start_run(run_name="ensemble_outlier"):
        mlflow.log_params({
            "model_type": "EnsembleOutlierDetector",
            "n_features": len(X.columns),
        })

        model = EnsembleOutlierDetector()
        model.fit(X)

        predictions = model.predict(X)
        n_anomalies = (predictions == -1).sum()

        mlflow.log_metrics({
            "n_anomalies": n_anomalies,
            "anomaly_rate": n_anomalies / len(X) * 100,
        })

        model_path = model.save()
        mlflow.log_artifact(str(model_path))

        print(f"Ensemble: {n_anomalies} anomalies detected ({n_anomalies/len(X)*100:.2f}%)")

    return model


def train_risk_engine(X: pd.DataFrame) -> RiskScoringEngine:
    """
    Train risk scoring engine.

    Args:
        X: Feature DataFrame

    Returns:
        Trained risk engine
    """
    print("Training risk scoring engine...")
    engine = RiskScoringEngine()
    engine.fit(X)
    return engine


def train_all_models() -> Dict[str, Any]:
    """
    Train all fraud detection models.

    Returns:
        Dictionary with all trained models
    """
    setup_mlflow()

    # Prepare data
    data = prepare_training_data()
    ml_dataset = data["ml_dataset"]

    # Get features
    feature_cols = get_feature_columns(ml_dataset)
    X = ml_dataset[feature_cols].copy()

    # Handle missing values
    X = X.fillna(X.median())

    # Convert boolean
    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)

    print(f"\nTraining with {len(X)} samples and {len(feature_cols)} features")
    print(f"Features: {feature_cols}\n")

    # Train models
    models = {}

    print("=" * 50)
    print("Training Isolation Forest...")
    models["isolation_forest"] = train_isolation_forest(X)

    print("=" * 50)
    print("Training K-Means...")
    models["kmeans"] = train_kmeans(X)

    print("=" * 50)
    print("Training Ensemble...")
    models["ensemble"] = train_ensemble(X)

    print("=" * 50)
    print("Training Risk Engine...")
    models["risk_engine"] = train_risk_engine(X)

    print("\n" + "=" * 50)
    print("All models trained successfully!")
    print(f"Models saved to: {OUTPUT_DIR / 'models'}")

    return models


if __name__ == "__main__":
    train_all_models()
