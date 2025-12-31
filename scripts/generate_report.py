#!/usr/bin/env python3
"""
Report generation script.
"""
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import OUTPUT_DIR
from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.driver_features import create_driver_features
from src.features.customer_features import create_customer_features
from src.features.aggregations import get_overall_statistics
from src.analysis.fraud_patterns import analyze_all_fraud_patterns, generate_fraud_report
from src.analysis.geographic import get_regional_summary
from src.analysis.temporal import get_temporal_summary


def main():
    """Generate comprehensive fraud detection report."""
    print("=" * 50)
    print("Walmart Fraud Detection - Report Generation")
    print("=" * 50)

    # Load data
    print("\nLoading data...")
    raw_data = extract_all()
    data = transform_all(raw_data)

    orders = data["orders"]
    drivers = data["drivers"]
    customers = data["customers"]

    # Create features
    print("Creating features...")
    driver_features = create_driver_features(drivers, orders)
    customer_features = create_customer_features(customers, orders)

    # Generate statistics
    print("Generating statistics...")
    overall_stats = get_overall_statistics(orders, drivers, customers)
    regional_summary = get_regional_summary(orders)
    temporal_summary = get_temporal_summary(orders)

    # Run fraud detection
    print("Running fraud detection...")
    fraud_indicators = analyze_all_fraud_patterns(orders, drivers, customers)
    fraud_report = generate_fraud_report(fraud_indicators)

    # Compile report
    report = {
        "generated_at": datetime.now().isoformat(),
        "data_period": {
            "start": str(overall_stats["date_range_start"]),
            "end": str(overall_stats["date_range_end"]),
        },
        "overall_statistics": {
            "total_orders": overall_stats["total_orders"],
            "total_revenue": float(overall_stats["total_revenue"]),
            "missing_rate": overall_stats["overall_missing_rate"],
            "orders_with_missing": overall_stats["orders_with_missing"],
            "pct_orders_with_missing": overall_stats["pct_orders_with_missing"],
        },
        "fraud_summary": {
            "total_indicators": fraud_report["summary"]["total_indicators"],
            "high_risk_count": len(fraud_report["high_risk"]),
            "medium_risk_count": len(fraud_report["medium_risk"]),
            "low_risk_count": len(fraud_report["low_risk"]),
        },
        "regional_summary": {
            "total_regions": regional_summary["total_regions"],
            "best_performing": regional_summary["best_performing"],
            "worst_performing": regional_summary["worst_performing"],
        },
        "temporal_summary": {
            "trend_direction": temporal_summary["trend"]["direction"],
            "peak_month": temporal_summary["trend"]["peak_month"],
            "worst_day": temporal_summary["patterns"]["worst_day"],
            "worst_hour": temporal_summary["patterns"]["worst_hour"],
        },
        "high_risk_entities": fraud_report["high_risk"][:20],  # Top 20
    }

    # Save report
    report_path = OUTPUT_DIR / "reports" / f"fraud_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport saved to: {report_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("FRAUD DETECTION REPORT SUMMARY")
    print("=" * 50)
    print(f"\nData Period: {report['data_period']['start']} to {report['data_period']['end']}")
    print(f"\nOverall Statistics:")
    print(f"  - Total Orders: {report['overall_statistics']['total_orders']:,}")
    print(f"  - Total Revenue: ${report['overall_statistics']['total_revenue']:,.2f}")
    print(f"  - Missing Rate: {report['overall_statistics']['missing_rate']:.2f}%")
    print(f"  - Orders with Issues: {report['overall_statistics']['orders_with_missing']:,}")

    print(f"\nFraud Indicators:")
    print(f"  - Total Indicators: {report['fraud_summary']['total_indicators']}")
    print(f"  - High Risk: {report['fraud_summary']['high_risk_count']}")
    print(f"  - Medium Risk: {report['fraud_summary']['medium_risk_count']}")
    print(f"  - Low Risk: {report['fraud_summary']['low_risk_count']}")

    print(f"\nRegional Analysis:")
    if report['regional_summary']['worst_performing']:
        worst = report['regional_summary']['worst_performing'][0]
        print(f"  - Highest Risk Region: {worst['region']} ({worst['missing_rate']:.2f}%)")
    if report['regional_summary']['best_performing']:
        best = report['regional_summary']['best_performing'][0]
        print(f"  - Lowest Risk Region: {best['region']} ({best['missing_rate']:.2f}%)")

    print(f"\nTemporal Patterns:")
    print(f"  - Trend: {report['temporal_summary']['trend_direction']}")
    print(f"  - Worst Day: {report['temporal_summary']['worst_day']}")
    print(f"  - Worst Hour: {report['temporal_summary']['worst_hour']}:00")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
