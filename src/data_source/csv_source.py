"""
CSV Data Source Implementation

Loads data from CSV files using the existing ETL extractors and transformers.
Normalizes the pivot format of missing_items to match the database format.
"""
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

from src.data_source.base import DataSource
from src.etl.extractors import (
    extract_orders,
    extract_customers,
    extract_drivers,
    extract_products,
    extract_missing_items,
)
from src.etl.transformers import (
    transform_orders,
    transform_customers,
    transform_drivers,
    transform_products,
    transform_missing_items,
)


class CSVDataSource(DataSource):
    """
    Data source implementation that reads from CSV files.

    This implementation:
    - Uses existing ETL extractors and transformers
    - Converts missing_items from pivot format to normalized format
    - Ensures column names match the database output format
    """

    def __init__(self):
        """Initialize the CSV data source."""
        self._products_cache: Optional[pd.DataFrame] = None

    @property
    def source_type(self) -> str:
        """Return 'csv' as the source type."""
        return "csv"

    def load_orders(self) -> pd.DataFrame:
        """
        Load and transform orders from CSV.

        Returns:
            DataFrame with orders data matching database format.
        """
        df = extract_orders()
        df = transform_orders(df)

        # Ensure column consistency with database output
        # Database returns order_id as string, ensure same here
        if 'order_id' in df.columns:
            df['order_id'] = df['order_id'].astype(str)

        # Database returns region directly (already done by transformer)
        return df

    def load_drivers(self) -> pd.DataFrame:
        """
        Load and transform drivers from CSV.

        Returns:
            DataFrame with drivers data matching database format.
        """
        df = extract_drivers()
        df = transform_drivers(df)

        # Transformer already outputs 'trips' column
        # Database uses 'total_trips as trips' alias
        return df

    def load_customers(self) -> pd.DataFrame:
        """
        Load and transform customers from CSV.

        Returns:
            DataFrame with customers data matching database format.
        """
        df = extract_customers()
        df = transform_customers(df)

        # Column already named customer_age by transformer
        return df

    def load_products(self) -> pd.DataFrame:
        """
        Load and transform products from CSV.

        Returns:
            DataFrame with products data matching database format.
        """
        df = extract_products()
        df = transform_products(df)

        # Transformer already fixes typo: produc_id -> product_id
        return df

    def load_missing_items(self) -> pd.DataFrame:
        """
        Load and transform missing items from CSV, converting to normalized format.

        The CSV uses pivot format (product_id_1, product_id_2, product_id_3),
        but the dashboard expects normalized format (one row per item).

        Returns:
            DataFrame with missing items in normalized format, matching database output.
        """
        df = extract_missing_items()
        df = transform_missing_items(df)

        # Convert pivot format to normalized format
        normalized_rows: List[Dict[str, Any]] = []
        item_counter = 1

        products_df = self.load_products()

        for _, row in df.iterrows():
            order_id = row['order_id']

            for position, col in enumerate(['product_id_1', 'product_id_2', 'product_id_3'], start=1):
                product_id = row.get(col)

                # Skip if product_id is NaN or None
                if pd.isna(product_id) or product_id is None:
                    continue

                # Ensure product_id is string
                product_id = str(product_id).strip()

                # Look up product details
                product_info = products_df[products_df['product_id'] == product_id]
                product_name = product_info['product_name'].iloc[0] if len(product_info) > 0 else None
                product_price = product_info['price'].iloc[0] if len(product_info) > 0 else None
                category = product_info['category'].iloc[0] if len(product_info) > 0 else None

                normalized_rows.append({
                    'missing_item_id': item_counter,
                    'order_id': order_id,
                    'product_id': product_id,
                    'item_position': position,
                    'product_name': product_name,
                    'product_price': product_price,
                    'category': category,
                })
                item_counter += 1

        result = pd.DataFrame(normalized_rows)

        # If no missing items, return empty DataFrame with correct columns
        if len(result) == 0:
            result = pd.DataFrame(columns=[
                'missing_item_id', 'order_id', 'product_id', 'item_position',
                'product_name', 'product_price', 'category'
            ])

        return result

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Calculate summary statistics from CSV data.

        Returns:
            Dictionary with summary statistics.
        """
        orders = self.load_orders()
        drivers = self.load_drivers()
        customers = self.load_customers()
        products = self.load_products()
        missing_items = self.load_missing_items()

        # Calculate statistics
        stats = {
            'total_orders': int(len(orders)),
            'total_drivers': int(len(drivers)),
            'total_customers': int(len(customers)),
            'total_products': int(len(products)),
            'total_missing_items': int(len(missing_items)),
            'sum_items_missing': int(orders['items_missing'].sum()),
            'total_order_value': float(orders['order_amount'].sum()),
            'min_date': orders['order_date'].min() if len(orders) > 0 else None,
            'max_date': orders['order_date'].max() if len(orders) > 0 else None,
        }

        return stats

    def is_available(self) -> bool:
        """
        Check if CSV files are accessible.

        Returns:
            True if the data directory and files exist.
        """
        try:
            from src.config.settings import DATA_FILES

            # Check if at least the orders file exists
            orders_path = DATA_FILES.get('orders')
            if orders_path is None:
                return False

            return orders_path.exists()
        except Exception:
            return False
