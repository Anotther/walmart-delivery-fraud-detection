"""
Database Data Source Implementation

Wraps the existing database connection module to implement the DataSource interface.
Provides transparent access to PostgreSQL data for the dashboard.
"""
from typing import Dict, Any

import pandas as pd

from src.data_source.base import DataSource
from src.database.connection import (
    load_orders as db_load_orders,
    load_drivers as db_load_drivers,
    load_customers as db_load_customers,
    load_products as db_load_products,
    load_missing_items as db_load_missing_items,
    get_summary_stats as db_get_summary_stats,
    test_connection,
)


class DatabaseDataSource(DataSource):
    """
    Data source implementation that reads from PostgreSQL.

    This implementation wraps the existing database connection functions
    to provide a consistent interface for the dashboard.
    """

    @property
    def source_type(self) -> str:
        """Return 'database' as the source type."""
        return "database"

    def load_orders(self) -> pd.DataFrame:
        """
        Load orders from PostgreSQL.

        Returns:
            DataFrame with orders data.
        """
        return db_load_orders()

    def load_drivers(self) -> pd.DataFrame:
        """
        Load drivers from PostgreSQL.

        Returns:
            DataFrame with drivers data.
        """
        return db_load_drivers()

    def load_customers(self) -> pd.DataFrame:
        """
        Load customers from PostgreSQL.

        Returns:
            DataFrame with customers data.
        """
        return db_load_customers()

    def load_products(self) -> pd.DataFrame:
        """
        Load products from PostgreSQL.

        Returns:
            DataFrame with products data.
        """
        return db_load_products()

    def load_missing_items(self) -> pd.DataFrame:
        """
        Load missing items from PostgreSQL (already in normalized format).

        Returns:
            DataFrame with missing items data in normalized format.
        """
        return db_load_missing_items()

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics from PostgreSQL.

        Returns:
            Dictionary with summary statistics.
        """
        return db_get_summary_stats()

    def is_available(self) -> bool:
        """
        Check if PostgreSQL connection is available.

        Returns:
            True if the database connection is successful.
        """
        return test_connection()
