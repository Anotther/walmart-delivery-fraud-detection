"""
Risk Thresholds Configuration

Centralized configuration for all risk scoring and analysis thresholds.
This module provides a single source of truth for threshold values
used across the fraud detection system.

Thresholds can be overridden via environment variables:
- RISK_CRITICAL_THRESHOLD: High-risk threshold (default: 75)
- RISK_HIGH_THRESHOLD: High-risk threshold (default: 50)
- RISK_MEDIUM_THRESHOLD: Medium-risk threshold (default: 25)
- RISK_ALERT_THRESHOLD: Alert threshold (default: 70)
- MISSING_RATE_DRIVER_THRESHOLD: Driver missing rate threshold (default: 20)
- MISSING_RATE_ORDER_THRESHOLD: Order missing rate threshold (default: 50)
- MISSING_RATE_FRAUD_THRESHOLD: Fraud pattern missing rate threshold (default: 50)
- GEOGRAPHIC_RANK_THRESHOLD: Geographic rank threshold (default: 75)

Usage:
    >>> from src.config.risk_thresholds import RiskThresholds
    >>>
    >>> # Access category boundaries
    >>> if risk_score >= RiskThresholds.CRITICAL:
    >>>     print("Critical risk detected")
    >>>
    >>> # Check if threshold is exceeded
    >>> if RiskThresholds.is_critical_risk(score):
    >>>     send_alert()

"""
import os
from typing import Dict, Tuple
from dataclasses import dataclass

# Load thresholds from environment variables or use defaults
_CRITICAL_THRESHOLD = float(os.getenv("RISK_CRITICAL_THRESHOLD", "75.0"))
_HIGH_THRESHOLD = float(os.getenv("RISK_HIGH_THRESHOLD", "50.0"))
_MEDIUM_THRESHOLD = float(os.getenv("RISK_MEDIUM_THRESHOLD", "25.0"))
_LOW_THRESHOLD = 0.0

_ALERT_THRESHOLD = float(os.getenv("RISK_ALERT_THRESHOLD", "70.0"))
_MISSING_RATE_DRIVER_THRESHOLD = float(os.getenv("MISSING_RATE_DRIVER_THRESHOLD", "20.0"))
_MISSING_RATE_ORDER_THRESHOLD = float(os.getenv("MISSING_RATE_ORDER_THRESHOLD", "50.0"))
_MISSING_RATE_FRAUD_THRESHOLD = float(os.getenv("MISSING_RATE_FRAUD_THRESHOLD", "50.0"))
_GEOGRAPHIC_RANK_THRESHOLD = float(os.getenv("GEOGRAPHIC_RANK_THRESHOLD", "75.0"))
_ANOMALY_STD_THRESHOLD = float(os.getenv("ANOMALY_STD_THRESHOLD", "2.0"))


@dataclass
class RiskThresholds:
    """
    Central container for all risk thresholds.

    Provides convenient methods for checking risk categories
    and validating risk scores.

    Attributes:
        CRITICAL: Threshold for critical risk (default: 75)
        HIGH: Threshold for high risk (default: 50)
        MEDIUM: Threshold for medium risk (default: 25)
        LOW: Threshold for low risk (default: 0)

    Example:
        >>> if risk_score >= RiskThresholds.CRITICAL:
        >>>     handle_critical_case()
        >>> category = RiskThresholds.get_category(risk_score)
        >>> assert category in ['Critical', 'High', 'Medium', 'Low']
    """

    # Risk score categories (0-100 scale)
    CRITICAL: float = _CRITICAL_THRESHOLD
    HIGH: float = _HIGH_THRESHOLD
    MEDIUM: float = _MEDIUM_THRESHOLD
    LOW: float = _LOW_THRESHOLD

    # Alert thresholds
    ALERT: float = _ALERT_THRESHOLD

    # Missing rate thresholds
    MISSING_RATE_DRIVER: float = _MISSING_RATE_DRIVER_THRESHOLD
    MISSING_RATE_ORDER: float = _MISSING_RATE_ORDER_THRESHOLD
    MISSING_RATE_FRAUD: float = _MISSING_RATE_FRAUD_THRESHOLD

    # Geographic thresholds
    GEOGRAPHIC_RANK: float = _GEOGRAPHIC_RANK_THRESHOLD

    # Statistical thresholds
    ANOMALY_STD: float = _ANOMALY_STD_THRESHOLD

    # Temporal thresholds
    WEEKEND_START_DAY: int = 5  # Friday (0=Monday, 6=Sunday)
    MONTH_START_DAY: int = 7   # First 7 days of month
    MONTH_END_DAY: int = 24     # Last 7+ days of month

    @classmethod
    def get_category(cls, score: float) -> str:
        """
        Get risk category for a given risk score.

        Args:
            score: Risk score (0-100)

        Returns:
            Risk category: 'Critical', 'High', 'Medium', or 'Low'

        Example:
            >>> category = RiskThresholds.get_category(85)
            >>> assert category == 'Critical'
        """
        if score >= cls.CRITICAL:
            return 'Critical'
        elif score >= cls.HIGH:
            return 'High'
        elif score >= cls.MEDIUM:
            return 'Medium'
        else:
            return 'Low'

    @classmethod
    def is_critical_risk(cls, score: float) -> bool:
        """
        Check if score indicates critical risk.

        Args:
            score: Risk score (0-100)

        Returns:
            True if score >= critical threshold

        Example:
            >>> if RiskThresholds.is_critical_risk(risk_score):
            >>>     send_alert()
        """
        return score >= cls.CRITICAL

    @classmethod
    def is_high_risk(cls, score: float) -> bool:
        """
        Check if score indicates high or critical risk.

        Args:
            score: Risk score (0-100)

        Returns:
            True if score >= high threshold

        Example:
            >>> if RiskThresholds.is_high_risk(risk_score):
            >>>     flag_for_review()
        """
        return score >= cls.HIGH

    @classmethod
    def is_medium_or_higher(cls, score: float) -> bool:
        """
        Check if score indicates medium, high, or critical risk.

        Args:
            score: Risk score (0-100)

        Returns:
            True if score >= medium threshold

        Example:
            >>> if RiskThresholds.is_medium_or_higher(risk_score):
            >>>     monitor_closely()
        """
        return score >= cls.MEDIUM

    @classmethod
    def is_alert_level(cls, score: float) -> bool:
        """
        Check if score triggers an alert.

        Args:
            score: Risk score (0-100)

        Returns:
            True if score >= alert threshold

        Example:
            >>> if RiskThresholds.is_alert_level(risk_score):
            >>>     trigger_alert()
        """
        return score >= cls.ALERT

    @classmethod
    def validate_score(cls, score: float) -> Tuple[bool, str]:
        """
        Validate a risk score is within acceptable range.

        Args:
            score: Risk score to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = RiskThresholds.validate_score(105)
            >>> assert not is_valid
            >>> assert 'out of range' in error.lower()
        """
        if not isinstance(score, (int, float)):
            return False, "Score must be numeric"

        if score < 0:
            return False, "Score cannot be negative"

        if score > 100:
            return False, "Score cannot exceed 100"

        return True, ""

    @classmethod
    def to_dict(cls) -> Dict[str, float]:
        """
        Export all thresholds as dictionary.

        Returns:
            Dictionary with all threshold values

        Example:
            >>> thresholds = RiskThresholds.to_dict()
            >>> assert thresholds['CRITICAL'] == 75.0
        """
        return {
            'CRITICAL': cls.CRITICAL,
            'HIGH': cls.HIGH,
            'MEDIUM': cls.MEDIUM,
            'LOW': cls.LOW,
            'ALERT': cls.ALERT,
            'MISSING_RATE_DRIVER': cls.MISSING_RATE_DRIVER,
            'MISSING_RATE_ORDER': cls.MISSING_RATE_ORDER,
            'MISSING_RATE_FRAUD': cls.MISSING_RATE_FRAUD,
            'GEOGRAPHIC_RANK': cls.GEOGRAPHIC_RANK,
            'ANOMALY_STD': cls.ANOMALY_STD,
            'WEEKEND_START_DAY': cls.WEEKEND_START_DAY,
            'MONTH_START_DAY': cls.MONTH_START_DAY,
            'MONTH_END_DAY': cls.MONTH_END_DAY,
        }

    @classmethod
    def print_configuration(cls) -> None:
        """Print current threshold configuration."""
        print("=" * 60)
        print("RISK THRESHOLDS CONFIGURATION")
        print("=" * 60)
        print(f"Risk Categories (0-100 scale):")
        print(f"  - CRITICAL:  >= {cls.CRITICAL}")
        print(f"  - HIGH:      >= {cls.HIGH}")
        print(f"  - MEDIUM:    >= {cls.MEDIUM}")
        print(f"  - LOW:       >= {cls.LOW}")
        print(f"\nAlert Thresholds:")
        print(f"  - ALERT_THRESHOLD:  {cls.ALERT}")
        print(f"\nMissing Rate Thresholds:")
        print(f"  - DRIVER:     {cls.MISSING_RATE_DRIVER}%")
        print(f"  - ORDER:      {cls.MISSING_RATE_ORDER}%")
        print(f"  - FRAUD:      {cls.MISSING_RATE_FRAUD}%")
        print(f"\nOther Thresholds:")
        print(f"  - GEOGRAPHIC_RANK:  {cls.GEOGRAPHIC_RANK}%")
        print(f"  - ANOMALY_STD:     {cls.ANOMALY_STD}σ")
        print(f"\nTemporal Thresholds:")
        print(f"  - WEEKEND_START_DAY: {cls.WEEKEND_START_DAY} (0=Mon, 6=Sun)")
        print(f"  - MONTH_START_DAY:   {cls.MONTH_START_DAY}")
        print(f"  - MONTH_END_DAY:     {cls.MONTH_END_DAY}")
        print("=" * 60)


# Legacy compatibility - these will be deprecated
RISK_THRESHOLDS = {
    'low': _MEDIUM_THRESHOLD,
    'medium': _HIGH_THRESHOLD,
    'high': _CRITICAL_THRESHOLD
}


if __name__ == "__main__":
    # Test the configuration
    RiskThresholds.print_configuration()

    # Test category detection
    test_scores = [0, 10, 25, 35, 50, 60, 75, 85, 95, 100]
    print("\nCategory Detection Tests:")
    print("-" * 60)
    for score in test_scores:
        category = RiskThresholds.get_category(score)
        print(f"  Score {score:6.1f} -> {category:8s} (is_critical={RiskThresholds.is_critical_risk(score)})")

    # Test validation
    print("\nValidation Tests:")
    print("-" * 60)
    for score in [0, 50, 100, -1, 101, "invalid"]:
        is_valid, error = RiskThresholds.validate_score(score)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  Score {str(score):10s} -> {status:8s} {error}")
