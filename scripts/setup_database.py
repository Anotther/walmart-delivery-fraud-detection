#!/usr/bin/env python3
"""
Database setup script.
Creates tables and loads initial data from CSV files.
"""
import sys
from pathlib import Path
from typing import Iterable

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.database import test_connection, engine
from src.config.settings import BASE_DIR
from src.etl.extractors import extract_all, get_data_info
from src.etl.transformers import transform_all, validate_data
from src.etl.loaders import load_all, get_table_counts
from sqlalchemy import text

SQL_FILES = (
    "001_create_schema.sql",
    "002_create_views.sql",
)


def _execute_sql_statements(conn, sql_text: str) -> None:
    statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]
    for statement in statements:
        conn.execute(text(statement))


def _get_schema_file_paths() -> Iterable[Path]:
    sql_dir = BASE_DIR / "src" / "database" / "sql"
    return (sql_dir / name for name in SQL_FILES)


def create_schema():
    """Create canonical database schema and analytical views."""
    file_paths = list(_get_schema_file_paths())
    missing_files = [path for path in file_paths if not path.exists()]
    if missing_files:
        print("Schema SQL files not found:")
        for path in missing_files:
            print(f"  - {path}")
        return False

    print("Creating canonical schema (walmart_fraud)...")
    try:
        with engine.begin() as conn:
            for sql_path in file_paths:
                print(f"  Applying {sql_path.name}...")
                sql_text = sql_path.read_text(encoding="utf-8")
                _execute_sql_statements(conn, sql_text)
    except Exception as exc:
        print(f"ERROR: Failed to create schema: {exc}")
        return False

    print("Schema and views created successfully.")
    return True


def run_etl():
    """Extract, transform, and load all data."""
    print("\n--- Extracting data from CSV files ---")
    info = get_data_info()
    for name, details in info.items():
        if details["exists"]:
            print(f"  {name}: {details['row_count']} rows, {details['size_mb']} MB")
        else:
            print(f"  {name}: FILE NOT FOUND at {details['path']}")
            return False

    raw_data = extract_all()

    print("\n--- Transforming data ---")
    transformed_data = transform_all(raw_data)

    print("\n--- Validating data ---")
    is_valid, issues = validate_data(transformed_data)
    if not is_valid:
        print("ERROR: Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("\n--- Loading data into PostgreSQL ---")
    try:
        results = load_all(transformed_data, truncate_first=True)
    except Exception as exc:
        print(f"ERROR: ETL load failed: {exc}")
        return False

    for table, count in results.items():
        print(f"  {table}: {count} rows loaded")

    print("\n--- Final table counts ---")
    counts = get_table_counts()
    for table, count in counts.items():
        print(f"  {table}: {count} rows")

    return True


def main():
    """Main entry point."""
    print("=" * 50)
    print("Walmart Fraud Detection - Database Setup")
    print("=" * 50)

    # Test connection
    print("\nTesting database connection...")
    if not test_connection():
        print("ERROR: Could not connect to database!")
        print("Please check your .env file and ensure PostgreSQL is running.")
        print("\nExpected connection settings:")
        print("  POSTGRES_HOST=localhost")
        print("  POSTGRES_PORT=5432")
        print("  POSTGRES_DB=walmart_fraud")
        print("  POSTGRES_USER=postgres")
        print("  POSTGRES_PASSWORD=your_password")
        return 1

    print("Database connection successful!")

    # Create schema
    if not create_schema():
        return 2

    # Run ETL
    if not run_etl():
        return 3

    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
