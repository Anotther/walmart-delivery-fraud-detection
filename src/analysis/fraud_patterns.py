"""
Fraud pattern detection and analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class FraudIndicator:
    """Represents a fraud indicator with score and details."""
    entity_type: str  # 'driver', 'customer', 'order', 'region'
    entity_id: str
    indicator_name: str
    score: float  # 0-100
    details: Dict[str, Any]


def detect_driver_fraud_patterns(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    threshold_std: float = 2.0
) -> List[FraudIndicator]:
    """
    Detect fraud patterns related to drivers.

    Patterns checked:
    - High missing rate compared to average
    - High percentage of orders with missing items
    - Unusual delivery time patterns

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        threshold_std: Standard deviations for anomaly

    Returns:
        List of FraudIndicator objects
    """
    indicators = []

    # Calculate driver statistics
    driver_stats = orders_df.groupby("driver_id").agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
    }).reset_index()

    driver_stats.columns = ["driver_id", "total_orders", "items_missing", "items_delivered"]
    driver_stats["total_items"] = driver_stats["items_delivered"] + driver_stats["items_missing"]
    driver_stats["missing_rate"] = np.where(
        driver_stats["total_items"] > 0,
        driver_stats["items_missing"] / driver_stats["total_items"] * 100,
        0
    )

    # Count orders with missing items per driver
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("driver_id").size()
    driver_stats["orders_with_missing"] = driver_stats["driver_id"].map(orders_with_missing).fillna(0)
    driver_stats["pct_orders_with_missing"] = (
        driver_stats["orders_with_missing"] / driver_stats["total_orders"] * 100
    )

    # Calculate thresholds
    avg_missing_rate = driver_stats["missing_rate"].mean()
    std_missing_rate = driver_stats["missing_rate"].std()
    high_missing_threshold = avg_missing_rate + threshold_std * std_missing_rate

    avg_pct_orders = driver_stats["pct_orders_with_missing"].mean()
    std_pct_orders = driver_stats["pct_orders_with_missing"].std()
    high_pct_threshold = avg_pct_orders + threshold_std * std_pct_orders

    # Find suspicious drivers
    for _, row in driver_stats.iterrows():
        score = 0
        details = {}

        # Check missing rate
        if row["missing_rate"] > high_missing_threshold:
            score += 40
            details["missing_rate_anomaly"] = {
                "value": row["missing_rate"],
                "threshold": high_missing_threshold,
                "deviation": (row["missing_rate"] - avg_missing_rate) / std_missing_rate if std_missing_rate > 0 else 0
            }

        # Check percentage of orders with issues
        if row["pct_orders_with_missing"] > high_pct_threshold:
            score += 35
            details["pct_orders_anomaly"] = {
                "value": row["pct_orders_with_missing"],
                "threshold": high_pct_threshold,
            }

        # Check absolute volume of missing items
        if row["items_missing"] > driver_stats["items_missing"].quantile(0.95):
            score += 25
            details["volume_anomaly"] = {
                "value": row["items_missing"],
                "percentile": 95
            }

        if score > 0:
            indicators.append(FraudIndicator(
                entity_type="driver",
                entity_id=row["driver_id"],
                indicator_name="suspicious_driver_pattern",
                score=min(score, 100),
                details=details
            ))

    return indicators


def detect_customer_fraud_patterns(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    threshold_std: float = 2.0
) -> List[FraudIndicator]:
    """
    Detect fraud patterns related to customers.

    Patterns checked:
    - High frequency of missing item reports
    - Consistent pattern of reporting missing items
    - High value items reported missing

    Args:
        orders_df: Orders DataFrame
        customers_df: Customers DataFrame
        threshold_std: Standard deviations for anomaly

    Returns:
        List of FraudIndicator objects
    """
    indicators = []

    # Calculate customer statistics
    customer_stats = orders_df.groupby("customer_id").agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_amount": "sum",
    }).reset_index()

    customer_stats.columns = [
        "customer_id", "total_orders", "items_missing",
        "items_delivered", "total_spent"
    ]
    customer_stats["total_items"] = customer_stats["items_delivered"] + customer_stats["items_missing"]
    customer_stats["missing_rate"] = np.where(
        customer_stats["total_items"] > 0,
        customer_stats["items_missing"] / customer_stats["total_items"] * 100,
        0
    )

    # Count orders with missing items
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("customer_id").size()
    customer_stats["orders_with_missing"] = customer_stats["customer_id"].map(orders_with_missing).fillna(0)
    customer_stats["pct_orders_with_missing"] = (
        customer_stats["orders_with_missing"] / customer_stats["total_orders"] * 100
    )

    # Calculate thresholds
    avg_missing_rate = customer_stats["missing_rate"].mean()
    std_missing_rate = customer_stats["missing_rate"].std()
    high_missing_threshold = avg_missing_rate + threshold_std * std_missing_rate

    # Find suspicious customers (only those with multiple orders)
    for _, row in customer_stats[customer_stats["total_orders"] >= 2].iterrows():
        score = 0
        details = {}

        # Check missing rate
        if row["missing_rate"] > high_missing_threshold:
            score += 35
            details["missing_rate_anomaly"] = {
                "value": row["missing_rate"],
                "threshold": high_missing_threshold,
            }

        # Check consistency of reporting (all orders have missing items)
        if row["pct_orders_with_missing"] == 100 and row["total_orders"] >= 3:
            score += 40
            details["consistent_reporting"] = {
                "orders": row["total_orders"],
                "all_with_missing": True
            }

        # Check if high spender with high missing rate
        if (row["total_spent"] > customer_stats["total_spent"].quantile(0.75) and
                row["missing_rate"] > avg_missing_rate * 1.5):
            score += 25
            details["high_value_pattern"] = {
                "total_spent": row["total_spent"],
                "missing_rate": row["missing_rate"]
            }

        if score > 0:
            indicators.append(FraudIndicator(
                entity_type="customer",
                entity_id=row["customer_id"],
                indicator_name="suspicious_customer_pattern",
                score=min(score, 100),
                details=details
            ))

    return indicators


def detect_collusion_patterns(
    orders_df: pd.DataFrame,
    min_interactions: int = 3,
    threshold_rate: float = 50.0
) -> List[FraudIndicator]:
    """
    Detect potential collusion between drivers and customers.

    Patterns checked:
    - Same driver-customer pair with high missing rate
    - Unusual frequency of interactions

    Args:
        orders_df: Orders DataFrame
        min_interactions: Minimum interactions to consider
        threshold_rate: Missing rate threshold

    Returns:
        List of FraudIndicator objects
    """
    indicators = []

    # Calculate driver-customer interactions
    interactions = orders_df.groupby(["driver_id", "customer_id"]).agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
    }).reset_index()

    interactions.columns = [
        "driver_id", "customer_id", "interactions",
        "items_missing", "items_delivered"
    ]
    interactions["total_items"] = interactions["items_delivered"] + interactions["items_missing"]
    interactions["missing_rate"] = np.where(
        interactions["total_items"] > 0,
        interactions["items_missing"] / interactions["total_items"] * 100,
        0
    )

    # Find suspicious pairs
    suspicious = interactions[
        (interactions["interactions"] >= min_interactions) &
        (interactions["missing_rate"] >= threshold_rate)
    ]

    for _, row in suspicious.iterrows():
        score = min(row["missing_rate"], 100)

        indicators.append(FraudIndicator(
            entity_type="pair",
            entity_id=f"{row['driver_id']}_{row['customer_id']}",
            indicator_name="potential_collusion",
            score=score,
            details={
                "driver_id": row["driver_id"],
                "customer_id": row["customer_id"],
                "interactions": row["interactions"],
                "missing_rate": row["missing_rate"],
                "items_missing": row["items_missing"]
            }
        ))

    return indicators


def detect_regional_patterns(
    orders_df: pd.DataFrame,
    threshold_std: float = 2.0
) -> List[FraudIndicator]:
    """
    Detect fraud patterns related to specific regions.

    Args:
        orders_df: Orders DataFrame
        threshold_std: Standard deviations for anomaly

    Returns:
        List of FraudIndicator objects
    """
    indicators = []

    # Calculate regional statistics
    regional_stats = orders_df.groupby("region").agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_amount": "sum",
    }).reset_index()

    regional_stats.columns = [
        "region", "total_orders", "items_missing",
        "items_delivered", "total_revenue"
    ]
    regional_stats["total_items"] = regional_stats["items_delivered"] + regional_stats["items_missing"]
    regional_stats["missing_rate"] = np.where(
        regional_stats["total_items"] > 0,
        regional_stats["items_missing"] / regional_stats["total_items"] * 100,
        0
    )

    # Calculate thresholds
    avg_rate = regional_stats["missing_rate"].mean()
    std_rate = regional_stats["missing_rate"].std()
    threshold = avg_rate + threshold_std * std_rate

    # Find problematic regions
    for _, row in regional_stats.iterrows():
        if row["missing_rate"] > threshold:
            indicators.append(FraudIndicator(
                entity_type="region",
                entity_id=row["region"],
                indicator_name="high_risk_region",
                score=min(row["missing_rate"], 100),
                details={
                    "missing_rate": row["missing_rate"],
                    "threshold": threshold,
                    "total_orders": row["total_orders"],
                    "items_missing": row["items_missing"]
                }
            ))

    return indicators


def analyze_all_fraud_patterns(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    customers_df: pd.DataFrame
) -> Dict[str, List[FraudIndicator]]:
    """
    Run all fraud pattern detection analyses.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        customers_df: Customers DataFrame

    Returns:
        Dictionary with all fraud indicators by type
    """
    return {
        "driver_patterns": detect_driver_fraud_patterns(orders_df, drivers_df),
        "customer_patterns": detect_customer_fraud_patterns(orders_df, customers_df),
        "collusion_patterns": detect_collusion_patterns(orders_df),
        "regional_patterns": detect_regional_patterns(orders_df),
    }


def generate_fraud_report(indicators: Dict[str, List[FraudIndicator]]) -> Dict[str, Any]:
    """
    Generate a summary report from fraud indicators.

    Args:
        indicators: Dictionary of fraud indicators

    Returns:
        Summary report dictionary
    """
    report = {
        "summary": {
            "total_indicators": sum(len(v) for v in indicators.values()),
            "by_type": {k: len(v) for k, v in indicators.items()},
        },
        "high_risk": [],
        "medium_risk": [],
        "low_risk": [],
    }

    for indicator_type, indicator_list in indicators.items():
        for indicator in indicator_list:
            item = {
                "type": indicator_type,
                "entity_type": indicator.entity_type,
                "entity_id": indicator.entity_id,
                "indicator": indicator.indicator_name,
                "score": indicator.score,
                "details": indicator.details
            }

            if indicator.score >= 70:
                report["high_risk"].append(item)
            elif indicator.score >= 40:
                report["medium_risk"].append(item)
            else:
                report["low_risk"].append(item)

    # Sort by score
    for risk_level in ["high_risk", "medium_risk", "low_risk"]:
        report[risk_level] = sorted(
            report[risk_level],
            key=lambda x: x["score"],
            reverse=True
        )

    return report
