#!/usr/bin/env python3
"""
Database setup script.
Creates tables and loads initial data from CSV files.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.database import test_connection, engine
from src.config.settings import BASE_DIR
from src.etl.extractors import extract_all, get_data_info
from src.etl.transformers import transform_all, validate_data
from src.etl.loaders import load_all, get_table_counts
from sqlalchemy import text


def create_schema():
    """Create database schema from SQL file."""
    schema_path = BASE_DIR / "src" / "database" / "schemas.sql"

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return False

    print("Creating database schema...")
    with open(schema_path) as f:
        schema_sql = f.read()

    with engine.connect() as conn:
        # Execute each statement separately
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
        for statement in statements:
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    print(f"Warning: {e}")
        conn.commit()

    print("Schema created successfully!")
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
        print("Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("Continuing with load...")

    print("\n--- Loading data into PostgreSQL ---")
    results = load_all(transformed_data, truncate_first=True)
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
        sys.exit(1)

    print("Database connection successful!")

    # Create schema
    if not create_schema():
        sys.exit(1)

    # Run ETL
    if not run_etl():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
