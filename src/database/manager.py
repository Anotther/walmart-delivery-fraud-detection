"""
Database Manager Module

Provides robust database access with fallback mechanisms and graceful degradation.
Handles database connectivity issues by providing mock data when necessary.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import wraps
import warnings
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class DatabaseManager:
    """
    Manages database connectivity with fallback to mock data.

    Provides decorator-based error handling and graceful degradation
    when database is unavailable.

    Attributes:
        db_available: Boolean indicating if database is connected
        use_fallback: Boolean indicating if fallback mode is active
        fallback_ttl: Time-to-live for cached mock data in minutes

    Example:
        >>> db_manager = DatabaseManager()
        >>> db_manager.initialize()
        >>>
        >>> @db_manager.with_fallback
        >>> def load_data():
        >>>     # Database operation
        >>>     return pd.DataFrame(...)
        >>>
        >>> data = load_data()  # Returns cached data if DB is down
    """

    # Mock data cache
    _mock_cache: Dict[str, Tuple[Any, datetime]] = {}

    def __init__(self, fallback_ttl_minutes: int = 30):
        """
        Initialize database manager.

        Args:
            fallback_ttl_minutes: Time-to-live for mock data cache (default: 30 min)
        """
        self.db_available: bool = False
        self.use_fallback: bool = False
        self.fallback_ttl_minutes: int = fallback_ttl_minutes
        self._connection_tested: bool = False
        self._last_error: Optional[Exception] = None
        self._db_host: Optional[str] = None
        self._last_health_check: Optional[datetime] = None

    def initialize(self) -> bool:
        """
        Test database connection and set availability status.

        Returns:
            True if database is available, False otherwise
        """
        try:
            from src.database.connection import (
                get_connection,
                load_orders,
                load_drivers
            )

            # Test connection
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()

            # Test basic queries
            orders = pd.read_sql("SELECT COUNT(*) as count FROM orders", conn)
            drivers = pd.read_sql("SELECT COUNT(*) as count FROM drivers", conn)

            self.db_available = True
            self.use_fallback = False
            self._connection_tested = True
            self._last_health_check = datetime.now()
            self._last_error = None

            logger.info("Database connection established successfully")
            logger.info(f"Orders: {orders['count'].iloc[0]}, Drivers: {drivers['count'].iloc[0]}")

            return True

        except Exception as e:
            self.db_available = False
            self.use_fallback = True
            self._connection_tested = True
            self._last_error = e
            self._last_health_check = datetime.now()

            logger.warning(f"Database connection failed: {e}")
            logger.warning("Fallback mode enabled - using mock data")

            return False

    def check_health(self) -> Dict[str, Any]:
        """
        Check database health status.

        Returns:
            Dictionary with health status information
        """
        if not self._connection_tested:
            self.initialize()

        # Test connection periodically (every 5 minutes)
        if self._last_health_check and \
           (datetime.now() - self._last_health_check).seconds > 300:
            self.initialize()

        return {
            'database_available': self.db_available,
            'fallback_active': self.use_fallback,
            'last_check': self._last_health_check.isoformat() if self._last_health_check else None,
            'last_error': str(self._last_error) if self._last_error else None,
            'mock_cache_size': len(self._mock_cache)
        }

    def with_fallback(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to provide fallback for database operations.

        If database operation fails, returns cached mock data if available.
        Otherwise, generates new mock data.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function with fallback logic

        Example:
            >>> @db_manager.with_fallback
            >>> def load_orders():
            >>>     return pd.read_sql("SELECT * FROM orders", conn)
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache_key = f"{func.__name__}"

            # Try to execute function if database is available
            if self.db_available and not self.use_fallback:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.db_available = False
                    self.use_fallback = True
                    self._last_error = e

            # Check if we have cached mock data
            if cache_key in self._mock_cache:
                cached_data, cached_at = self._mock_cache[cache_key]
                age = datetime.now() - cached_at

                if age <= timedelta(minutes=self.fallback_ttl_minutes):
                    logger.info(f"Returning cached mock data for {func.__name__} (age: {age.seconds}s)")
                    return cached_data
                else:
                    # Cache expired, remove it
                    del self._mock_cache[cache_key]

            # Generate new mock data
            logger.warning(f"Generating mock data for {func.__name__}")
            mock_data = self._generate_mock_data(func.__name__)

            # Cache the mock data
            self._mock_cache[cache_key] = (mock_data, datetime.now())

            return mock_data

        return wrapper

    def _generate_mock_data(self, method_name: str) -> Any:
        """
        Generate mock data for specific methods.

        Args:
            method_name: Name of the method needing mock data

        Returns:
            Mock data appropriate for the method
        """
        # Map method names to mock data generators
        mock_generators = {
            'load_orders': self._mock_orders,
            'load_drivers': self._mock_drivers,
            'load_customers': self._mock_customers,
            'load_products': self._mock_products,
            'load_missing_items': self._mock_missing_items,
            'get_driver_summary': self._mock_driver_summary,
            'get_customer_summary': self._mock_customer_summary,
            'get_regional_summary': self._mock_regional_summary,
            'get_overview_metrics': self._mock_overview_metrics,
        }

        generator = mock_generators.get(method_name)

        if generator:
            return generator()
        else:
            # Default to empty DataFrame/Dict for unknown methods
            if 'summary' in method_name or 'metrics' in method_name:
                return {}
            return pd.DataFrame()

    def clear_mock_cache(self) -> None:
        """Clear all cached mock data."""
        self._mock_cache.clear()
        logger.info("Mock data cache cleared")

    def invalidate_key(self, key: str) -> None:
        """
        Invalidate a specific cache key.

        Args:
            key: Cache key to invalidate
        """
        if key in self._mock_cache:
            del self._mock_cache[key]
            logger.info(f"Invalidated cache key: {key}")

    # -------------------------------------------------------------------------
    # Mock Data Generators
    # -------------------------------------------------------------------------

    def _mock_orders(self) -> pd.DataFrame:
        """Generate mock orders data."""
        np.random.seed(42)
        n = 1000

        dates = pd.date_range('2023-01-01', '2023-12-31', periods=n)

        data = pd.DataFrame({
            'order_id': [f'ORD{i:06d}' for i in range(n)],
            'driver_id': [f'WDID{np.random.randint(10000, 10050)}' for _ in range(n)],
            'customer_id': [f'WCID{np.random.randint(1000, 2000)}' for _ in range(n)],
            'order_date': dates,
            'region': np.random.choice(['Orlando', 'Winter Park', 'Altamonte Springs', 'Apopka', 'Sanford'], n),
            'items_delivered': np.random.randint(1, 10, n),
            'items_missing': np.random.randint(0, 3, n),
            'order_amount': np.random.uniform(20, 500, n),
            'delivery_hour': [f'{h:02d}:00:00' for h in np.random.randint(6, 22, n)]
        })

        data['order_date'] = pd.to_datetime(data['order_date'])
        data['order_amount'] = data['order_amount'].round(2)

        return data

    def _mock_drivers(self) -> pd.DataFrame:
        """Generate mock drivers data."""
        np.random.seed(42)
        n = 50

        data = pd.DataFrame({
            'driver_id': [f'WDID{10000 + i}' for i in range(n)],
            'driver_name': [f'Driver {i+1}' for i in range(n)],
            'age': np.random.randint(22, 65, n),
            'trips': np.random.randint(10, 500, n)
        })

        return data

    def _mock_customers(self) -> pd.DataFrame:
        """Generate mock customers data."""
        np.random.seed(42)
        n = 200

        data = pd.DataFrame({
            'customer_id': [f'WCID{1000 + i}' for i in range(n)],
            'customer_name': [f'Customer {i+1}' for i in range(n)],
            'customer_age': np.random.randint(18, 80, n)
        })

        return data

    def _mock_products(self) -> pd.DataFrame:
        """Generate mock products data."""
        np.random.seed(42)
        n = 100

        categories = ['Electronics', 'Groceries', 'Health', 'Beauty', 'Home', 'Clothing']

        data = pd.DataFrame({
            'product_id': [f'PRD{i:04d}' for i in range(n)],
            'product_name': [f'Product {i+1}' for i in range(n)],
            'category': np.random.choice(categories, n),
            'price': np.random.uniform(5, 200, n).round(2)
        })

        return data

    def _mock_missing_items(self) -> pd.DataFrame:
        """Generate mock missing items data."""
        np.random.seed(42)
        n = 300

        data = pd.DataFrame({
            'order_id': [f'ORD{np.random.randint(0, 1000):06d}' for _ in range(n)],
            'product_id': [f'PRD{np.random.randint(0, 100):04d}' for _ in range(n)],
            'missing_item_id': [f'MIS{i:06d}' for i in range(n)]
        })

        return data

    def _mock_driver_summary(self) -> pd.DataFrame:
        """Generate mock driver summary with risk scores."""
        np.random.seed(42)
        n = 50

        data = pd.DataFrame({
            'driver_id': [f'WDID{10000 + i}' for i in range(n)],
            'driver_name': [f'Driver {i+1}' for i in range(n)],
            'age': np.random.randint(22, 65, n),
            'trips': np.random.randint(10, 500, n),
            'orders_completed': np.random.randint(10, 200, n),
            'items_delivered': np.random.randint(50, 1000, n),
            'items_missing': np.random.randint(0, 30, n),
            'orders_with_missing': np.random.randint(0, 50, n),
            'total_revenue': np.random.uniform(5000, 50000, n).round(2),
            'missing_rate': np.random.uniform(0, 5, n).round(2),
            'pct_orders_with_missing': np.random.uniform(0, 10, n).round(2),
            'avg_order_value': np.random.uniform(50, 200, n).round(2),
            'risk_score': np.random.uniform(0, 100, n).round(2),
            'risk_category': np.random.choice(['Low', 'Low', 'Low', 'Medium', 'Medium', 'High', 'High', 'Critical'], n)
        })

        return data

    def _mock_customer_summary(self) -> pd.DataFrame:
        """Generate mock customer summary with risk scores."""
        np.random.seed(42)
        n = 200

        data = pd.DataFrame({
            'customer_id': [f'WCID{1000 + i}' for i in range(n)],
            'customer_name': [f'Customer {i+1}' for i in range(n)],
            'customer_age': np.random.randint(18, 80, n),
            'total_orders': np.random.randint(1, 50, n),
            'total_spent': np.random.uniform(100, 10000, n).round(2),
            'items_received': np.random.randint(5, 200, n),
            'items_reported_missing': np.random.randint(0, 10, n),
            'orders_with_claims': np.random.randint(0, 20, n),
            'claim_rate': np.random.uniform(0, 5, n).round(2),
            'pct_orders_with_claims': np.random.uniform(0, 15, n).round(2),
            'avg_order_value': np.random.uniform(50, 300, n).round(2),
            'risk_score': np.random.uniform(0, 100, n).round(2),
            'risk_category': np.random.choice(['Low', 'Low', 'Low', 'Medium', 'Medium', 'High', 'High', 'Critical'], n),
            'spending_segment': np.random.choice(['Low Value', 'Medium Value', 'High Value', 'Premium'], n)
        })

        return data

    def _mock_regional_summary(self) -> pd.DataFrame:
        """Generate mock regional summary."""
        np.random.seed(42)

        regions = ['Orlando', 'Winter Park', 'Altamonte Springs', 'Apopka', 'Sanford', 'Clermont']
        n = len(regions)

        data = pd.DataFrame({
            'region': regions,
            'total_orders': np.random.randint(150, 400, n),
            'total_revenue': np.random.uniform(30000, 90000, n).round(2),
            'avg_order_value': np.random.uniform(100, 250, n).round(2),
            'items_delivered': np.random.randint(500, 2000, n),
            'items_missing': np.random.randint(10, 50, n),
            'orders_with_missing': np.random.randint(5, 40, n),
            'unique_drivers': np.random.randint(8, 15, n),
            'unique_customers': np.random.randint(50, 150, n),
            'missing_rate': np.random.uniform(1, 4, n).round(2),
            'pct_orders_with_missing': np.random.uniform(2, 10, n).round(2),
            'orders_per_driver': np.random.uniform(15, 35, n).round(2),
            'orders_per_customer': np.random.uniform(2, 5, n).round(2),
            'revenue_share': np.random.uniform(10, 25, n).round(2),
            'risk_rank': range(1, n+1)
        })

        return data

    def _mock_overview_metrics(self) -> Dict:
        """Generate mock overview metrics."""
        return {
            'total_orders': 1500,
            'total_revenue': 450000.00,
            'avg_order_value': 150.00,
            'median_order_value': 125.00,
            'min_order_value': 20.00,
            'max_order_value': 500.00,
            'total_items_ordered': 8000,
            'total_items_delivered': 7500,
            'total_items_missing': 500,
            'overall_missing_rate': 6.25,
            'orders_with_missing': 250,
            'pct_orders_with_missing': 16.67,
            'total_drivers': 50,
            'active_drivers': 45,
            'total_customers': 800,
            'active_customers': 600,
            'total_regions': 6,
            'date_range_start': '2023-01-01',
            'date_range_end': '2023-12-31',
            'estimated_loss': 7500.00,
            'calculated_at': datetime.now().isoformat()
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


def reset_db_manager() -> None:
    """Reset the global database manager instance (useful for testing)."""
    global _db_manager
    _db_manager = None
