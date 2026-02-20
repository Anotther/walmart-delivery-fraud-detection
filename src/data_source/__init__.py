"""
Data Source Abstraction Layer

This module provides a Strategy pattern implementation for switching between
CSV files and PostgreSQL as data sources for the dashboard.

Usage:
    from src.data_source import get_data_source

    data_source = get_data_source()
    orders = data_source.load_orders()
    drivers = data_source.load_drivers()

Configuration:
    Set the DATA_SOURCE environment variable to 'csv' (default) or 'database'.

Example:
    # In .env file
    DATA_SOURCE=csv

    # Or
    DATA_SOURCE=database
"""

from src.data_source.base import DataSource
from src.data_source.csv_source import CSVDataSource
from src.data_source.database_source import DatabaseDataSource
from src.data_source.factory import (
    create_data_source,
    get_data_source,
    reset_data_source,
    get_available_data_source,
)

__all__ = [
    "DataSource",
    "CSVDataSource",
    "DatabaseDataSource",
    "create_data_source",
    "get_data_source",
    "reset_data_source",
    "get_available_data_source",
]
