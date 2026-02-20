"""
Data Source Abstraction Layer

This module provides a Strategy pattern implementation for switching between
CSV files and PostgreSQL as data sources for the dashboard.

Usage:
    from src.data_source import get_data_source

    data_source = get_data_source()
    orders = data_source.load_orders()
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

import pandas as pd


class DataSource(ABC):
    """
    Abstract base class for data sources.

    Defines the interface that all data source implementations must follow.
    This allows the dashboard to work transparently with CSV files or PostgreSQL.
    """

    @property
    @abstractmethod
    def source_type(self) -> str:
        """
        Return the type of this data source.

        Returns:
            str: 'csv' or 'database'
        """
        pass

    @abstractmethod
    def load_orders(self) -> pd.DataFrame:
        """
        Load orders data.

        Returns:
            DataFrame with columns:
            - order_id: str
            - order_date: date
            - order_amount: float
            - region: str
            - items_delivered: int
            - items_missing: int
            - delivery_hour: time
            - driver_id: str
            - customer_id: str
            - created_at: datetime (optional)
        """
        pass

    @abstractmethod
    def load_drivers(self) -> pd.DataFrame:
        """
        Load drivers data.

        Returns:
            DataFrame with columns:
            - driver_id: str
            - driver_name: str
            - age: int (nullable)
            - trips: int
        """
        pass

    @abstractmethod
    def load_customers(self) -> pd.DataFrame:
        """
        Load customers data.

        Returns:
            DataFrame with columns:
            - customer_id: str
            - customer_name: str
            - customer_age: int (nullable)
        """
        pass

    @abstractmethod
    def load_products(self) -> pd.DataFrame:
        """
        Load products data.

        Returns:
            DataFrame with columns:
            - product_id: str
            - product_name: str
            - category: str
            - price: float
        """
        pass

    @abstractmethod
    def load_missing_items(self) -> pd.DataFrame:
        """
        Load missing items data in normalized format.

        Returns:
            DataFrame with columns (normalized format):
            - missing_item_id: int (optional, synthetic for CSV)
            - order_id: str
            - product_id: str
            - item_position: int
            - product_name: str (optional, from join)
            - product_price: float (optional, from join)
            - category: str (optional, from join)
        """
        pass

    @abstractmethod
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics from the data source.

        Returns:
            Dictionary with summary statistics:
            - total_orders: int
            - total_drivers: int
            - total_customers: int
            - total_products: int
            - total_missing_items: int
            - sum_items_missing: int
            - total_order_value: float
            - min_date: date
            - max_date: date
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data source is available.

        Returns:
            True if the data source can be accessed, False otherwise.
        """
        pass
