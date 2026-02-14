#!/usr/bin/env python3
"""
ETL script - Extract, Transform, and Load data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.extractors import extract_all, get_data_info
from src.etl.transformers import transform_all, validate_data
from src.etl.loaders import load_all, get_table_counts


def main():
    """Run the ETL pipeline."""
    print("=" * 50)
    print("Walmart Fraud Detection - ETL Pipeline")
    print("=" * 50)

    # Extract
    print("\n--- Extracting data ---")
    info = get_data_info()
    for name, details in info.items():
        if details["exists"]:
            print(f"  {name}: {details['row_count']} rows")
        else:
            print(f"  {name}: NOT FOUND")
            return 1

    raw_data = extract_all()

    # Transform
    print("\n--- Transforming data ---")
    transformed_data = transform_all(raw_data)

    # Validate
    print("\n--- Validating data ---")
    is_valid, issues = validate_data(transformed_data)
    if not is_valid:
        print("ERROR: Validation failed")
        for issue in issues:
            print(f"  Warning: {issue}")
        return 2

    # Load
    print("\n--- Loading data ---")
    try:
        results = load_all(transformed_data, truncate_first=True)
    except Exception as exc:
        print(f"ERROR: Load failed: {exc}")
        return 3
    for table, count in results.items():
        print(f"  {table}: {count} rows loaded")

    # Verify
    print("\n--- Verification ---")
    counts = get_table_counts()
    for table, count in counts.items():
        print(f"  {table}: {count} rows")

    print("\n" + "=" * 50)
    print("ETL completed successfully!")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
