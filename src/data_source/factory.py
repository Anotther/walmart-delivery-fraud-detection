"""
Data Source Factory

Factory module for creating data source instances based on configuration.
Provides a singleton pattern for efficient reuse.
"""
from typing import Optional

from src.data_source.base import DataSource
from src.data_source.csv_source import CSVDataSource
from src.data_source.database_source import DatabaseDataSource


# Singleton instance
_data_source_instance: Optional[DataSource] = None


def create_data_source(source_type: str) -> DataSource:
    """
    Create a data source instance based on the specified type.

    Args:
        source_type: Type of data source ('csv' or 'database')

    Returns:
        DataSource instance

    Raises:
        ValueError: If source_type is not recognized
    """
    source_type = source_type.lower().strip()

    if source_type == "csv":
        return CSVDataSource()
    elif source_type in ("database", "postgres", "postgresql"):
        return DatabaseDataSource()
    else:
        raise ValueError(
            f"Unknown data source type: '{source_type}'. "
            f"Valid options: 'csv', 'database'"
        )


def get_data_source() -> DataSource:
    """
    Get the singleton data source instance based on environment configuration.

    The data source type is determined by the DATA_SOURCE environment variable.
    Defaults to 'csv' if not set.

    Returns:
        Singleton DataSource instance

    Environment Variables:
        DATA_SOURCE: 'csv' (default) or 'database'
    """
    global _data_source_instance

    if _data_source_instance is None:
        from src.config.settings import DATA_SOURCE
        _data_source_instance = create_data_source(DATA_SOURCE)

    return _data_source_instance


def reset_data_source() -> None:
    """
    Reset the singleton data source instance.

    This is useful for testing or when switching data sources at runtime.
    """
    global _data_source_instance
    _data_source_instance = None


def get_available_data_source() -> DataSource:
    """
    Get an available data source, with fallback to CSV if database is unavailable.

    This function attempts to use the configured data source, but will fall back
    to CSV if the database is configured but unavailable.

    Returns:
        Available DataSource instance
    """
    from src.config.settings import DATA_SOURCE

    configured_type = DATA_SOURCE.lower().strip()

    # If CSV is configured, just use it
    if configured_type == "csv":
        return get_data_source()

    # If database is configured, check availability
    if configured_type in ("database", "postgres", "postgresql"):
        try:
            ds = create_data_source("database")
            if ds.is_available():
                return ds
            else:
                # Fall back to CSV
                import logging
                logging.warning(
                    "Database data source unavailable, falling back to CSV"
                )
                return create_data_source("csv")
        except Exception as e:
            # Fall back to CSV on any error
            import logging
            logging.warning(
                f"Failed to connect to database: {e}. Falling back to CSV"
            )
            return create_data_source("csv")

    # Default to CSV for unknown types
    return get_data_source()
