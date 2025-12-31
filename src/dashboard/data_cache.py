"""
Dashboard Data Cache Module

Provides caching layer for dashboard data to improve performance.
Uses time-based cache invalidation and thread-safe operations.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from functools import wraps
import threading

from src.database.connection import (
    load_orders, load_drivers, load_customers, load_products,
    load_missing_items, get_summary_stats
)


class DashboardCache:
    """
    Thread-safe caching layer for dashboard data.

    Provides cached access to computed dashboard data with configurable
    TTL (Time To Live) for cache invalidation.

    Attributes:
        ttl_minutes: Cache time-to-live in minutes

    Example:
        >>> cache = DashboardCache(ttl_minutes=15)
        >>> metrics = cache.get_overview_metrics()
        >>> drivers = cache.get_driver_summary()
        >>> cache.refresh_all()  # Force refresh all caches
    """

    def __init__(self, ttl_minutes: int = 15):
        """
        Initialize the dashboard cache.

        Args:
            ttl_minutes: Cache time-to-live in minutes (default: 15)
        """
        self.ttl_minutes = ttl_minutes
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            cache_key: The cache key to check

        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self._cache:
            return False

        cache_entry = self._cache[cache_key]
        expiry = cache_entry.get('expiry')

        if expiry is None:
            return False

        return datetime.now() < expiry

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """
        Store data in cache with expiry time.

        Args:
            cache_key: The cache key
            data: Data to cache
        """
        with self._lock:
            self._cache[cache_key] = {
                'data': data,
                'expiry': datetime.now() + timedelta(minutes=self.ttl_minutes),
                'created_at': datetime.now()
            }

    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve data from cache if valid.

        Args:
            cache_key: The cache key

        Returns:
            Cached data or None if not valid
        """
        with self._lock:
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]['data']
            return None

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear cache entries.

        Args:
            cache_key: Specific key to clear, or None to clear all
        """
        with self._lock:
            if cache_key is None:
                self._cache.clear()
            elif cache_key in self._cache:
                del self._cache[cache_key]

    def refresh_all(self) -> None:
        """Force refresh all cached data."""
        self.clear_cache()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about current cache state.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            info = {
                'ttl_minutes': self.ttl_minutes,
                'cached_keys': list(self._cache.keys()),
                'cache_entries': {}
            }

            for key, entry in self._cache.items():
                info['cache_entries'][key] = {
                    'created_at': entry.get('created_at'),
                    'expiry': entry.get('expiry'),
                    'is_valid': self._is_cache_valid(key)
                }

            return info

    # -------------------------------------------------------------------------
    # Data Loading with Caching
    # -------------------------------------------------------------------------

    def _load_orders_with_features(self) -> pd.DataFrame:
        """Load orders and add derived features."""
        orders = load_orders()
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        orders['total_items'] = orders['items_delivered'] + orders['items_missing']
        orders['missing_rate'] = np.where(
            orders['total_items'] > 0,
            (orders['items_missing'] / orders['total_items']) * 100,
            0
        )
        orders['has_missing'] = orders['items_missing'] > 0
        orders['month'] = orders['order_date'].dt.month
        orders['month_name'] = orders['order_date'].dt.month_name()
        orders['day_of_week'] = orders['order_date'].dt.day_name()
        orders['day_of_week_num'] = orders['order_date'].dt.dayofweek
        return orders

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    def get_overview_metrics(self) -> Dict:
        """
        Get overview metrics for dashboard main page.

        Returns:
            Dictionary with all key metrics
        """
        cache_key = 'overview_metrics'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        orders = self._load_orders_with_features()
        drivers = load_drivers()
        customers = load_customers()

        total_items = orders['items_delivered'].sum() + orders['items_missing'].sum()
        total_missing = orders['items_missing'].sum()
        orders_with_missing = (orders['items_missing'] > 0).sum()

        metrics = {
            # Order metrics
            'total_orders': int(len(orders)),
            'total_revenue': float(orders['order_amount'].sum()),
            'avg_order_value': float(orders['order_amount'].mean()),
            'median_order_value': float(orders['order_amount'].median()),
            'min_order_value': float(orders['order_amount'].min()),
            'max_order_value': float(orders['order_amount'].max()),

            # Item metrics
            'total_items_ordered': int(total_items),
            'total_items_delivered': int(orders['items_delivered'].sum()),
            'total_items_missing': int(total_missing),
            'overall_missing_rate': float((total_missing / total_items * 100) if total_items > 0 else 0),

            # Orders with issues
            'orders_with_missing': int(orders_with_missing),
            'pct_orders_with_missing': float((orders_with_missing / len(orders) * 100) if len(orders) > 0 else 0),

            # Entity counts
            'total_drivers': int(len(drivers)),
            'active_drivers': int(orders['driver_id'].nunique()),
            'total_customers': int(len(customers)),
            'active_customers': int(orders['customer_id'].nunique()),
            'total_regions': int(orders['region'].nunique()),

            # Time range
            'date_range_start': str(orders['order_date'].min().date()),
            'date_range_end': str(orders['order_date'].max().date()),

            # Estimated loss (assuming average $15 per missing item)
            'estimated_loss': float(total_missing * 15),

            # Timestamp
            'calculated_at': datetime.now().isoformat()
        }

        self._set_cache(cache_key, metrics)
        return metrics

    def get_driver_summary(self) -> pd.DataFrame:
        """
        Get driver performance summary.

        Returns:
            DataFrame with driver summary metrics
        """
        cache_key = 'driver_summary'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        orders = self._load_orders_with_features()
        drivers = load_drivers()

        # Aggregate orders by driver
        driver_orders = orders.groupby('driver_id').agg({
            'order_id': 'count',
            'order_amount': 'sum',
            'items_delivered': 'sum',
            'items_missing': 'sum',
            'has_missing': 'sum'
        }).reset_index()

        driver_orders.columns = ['driver_id', 'orders_completed', 'total_revenue',
                                 'items_delivered', 'items_missing', 'orders_with_missing']

        # Calculate metrics
        driver_orders['total_items'] = driver_orders['items_delivered'] + driver_orders['items_missing']
        driver_orders['missing_rate'] = np.where(
            driver_orders['total_items'] > 0,
            (driver_orders['items_missing'] / driver_orders['total_items']) * 100,
            0
        )
        driver_orders['pct_orders_with_missing'] = (
            driver_orders['orders_with_missing'] / driver_orders['orders_completed'] * 100
        )
        driver_orders['avg_order_value'] = driver_orders['total_revenue'] / driver_orders['orders_completed']

        # Merge with driver info
        driver_summary = drivers.merge(driver_orders, on='driver_id', how='left')
        driver_summary = driver_summary.fillna(0)

        # Calculate risk score (0-100 scale)
        max_missing_rate = driver_summary['missing_rate'].max()
        max_pct_orders = driver_summary['pct_orders_with_missing'].max()

        driver_summary['risk_score'] = np.where(
            (max_missing_rate > 0) & (max_pct_orders > 0),
            (
                (driver_summary['missing_rate'] / max_missing_rate * 50) +
                (driver_summary['pct_orders_with_missing'] / max_pct_orders * 50)
            ),
            0
        )

        # Risk category
        driver_summary['risk_category'] = pd.cut(
            driver_summary['risk_score'],
            bins=[-1, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Critical']
        )

        result = driver_summary.sort_values('risk_score', ascending=False)
        self._set_cache(cache_key, result)
        return result

    def get_customer_summary(self) -> pd.DataFrame:
        """
        Get customer behavior summary.

        Returns:
            DataFrame with customer summary metrics
        """
        cache_key = 'customer_summary'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        orders = self._load_orders_with_features()
        customers = load_customers()

        # Aggregate orders by customer
        customer_orders = orders.groupby('customer_id').agg({
            'order_id': 'count',
            'order_amount': 'sum',
            'items_delivered': 'sum',
            'items_missing': 'sum',
            'has_missing': 'sum'
        }).reset_index()

        customer_orders.columns = ['customer_id', 'total_orders', 'total_spent',
                                   'items_received', 'items_reported_missing', 'orders_with_claims']

        # Calculate metrics
        customer_orders['total_items'] = customer_orders['items_received'] + customer_orders['items_reported_missing']
        customer_orders['claim_rate'] = np.where(
            customer_orders['total_items'] > 0,
            (customer_orders['items_reported_missing'] / customer_orders['total_items']) * 100,
            0
        )
        customer_orders['pct_orders_with_claims'] = (
            customer_orders['orders_with_claims'] / customer_orders['total_orders'] * 100
        )
        customer_orders['avg_order_value'] = customer_orders['total_spent'] / customer_orders['total_orders']

        # Merge with customer info
        customer_summary = customers.merge(customer_orders, on='customer_id', how='left')
        customer_summary = customer_summary.fillna(0)

        # Calculate risk score (0-100 scale)
        max_claim_rate = customer_summary['claim_rate'].max()
        max_pct_orders = customer_summary['pct_orders_with_claims'].max()

        customer_summary['risk_score'] = np.where(
            (max_claim_rate > 0) & (max_pct_orders > 0),
            (
                (customer_summary['claim_rate'] / max_claim_rate * 50) +
                (customer_summary['pct_orders_with_claims'] / max_pct_orders * 50)
            ),
            0
        )

        # Risk category
        customer_summary['risk_category'] = pd.cut(
            customer_summary['risk_score'],
            bins=[-1, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Critical']
        )

        # Spending segment
        customer_summary['spending_segment'] = pd.cut(
            customer_summary['total_spent'],
            bins=[-1, 500, 2000, 5000, float('inf')],
            labels=['Low Value', 'Medium Value', 'High Value', 'Premium']
        )

        result = customer_summary.sort_values('risk_score', ascending=False)
        self._set_cache(cache_key, result)
        return result

    def get_regional_summary(self) -> pd.DataFrame:
        """
        Get regional performance summary.

        Returns:
            DataFrame with regional metrics
        """
        cache_key = 'regional_summary'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        orders = self._load_orders_with_features()

        # Aggregate by region
        regional = orders.groupby('region').agg({
            'order_id': 'count',
            'order_amount': ['sum', 'mean'],
            'items_delivered': 'sum',
            'items_missing': 'sum',
            'driver_id': 'nunique',
            'customer_id': 'nunique',
            'has_missing': 'sum'
        }).reset_index()

        regional.columns = ['region', 'total_orders', 'total_revenue', 'avg_order_value',
                            'items_delivered', 'items_missing', 'unique_drivers',
                            'unique_customers', 'orders_with_missing']

        # Calculate metrics
        regional['total_items'] = regional['items_delivered'] + regional['items_missing']
        regional['missing_rate'] = np.where(
            regional['total_items'] > 0,
            (regional['items_missing'] / regional['total_items']) * 100,
            0
        )
        regional['pct_orders_with_missing'] = (
            regional['orders_with_missing'] / regional['total_orders'] * 100
        )
        regional['orders_per_driver'] = regional['total_orders'] / regional['unique_drivers']
        regional['orders_per_customer'] = regional['total_orders'] / regional['unique_customers']
        regional['revenue_share'] = regional['total_revenue'] / regional['total_revenue'].sum() * 100
        regional['risk_rank'] = regional['missing_rate'].rank(ascending=False).astype(int)

        result = regional.sort_values('missing_rate', ascending=False)
        self._set_cache(cache_key, result)
        return result

    def get_temporal_trends(self) -> Dict[str, pd.DataFrame]:
        """
        Get temporal trends data.

        Returns:
            Dictionary with monthly, daily, and hourly DataFrames
        """
        cache_key = 'temporal_trends'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        orders = self._load_orders_with_features()

        # Monthly trends
        monthly = orders.groupby('month').agg({
            'order_id': 'count',
            'order_amount': 'sum',
            'items_delivered': 'sum',
            'items_missing': 'sum',
            'has_missing': 'sum'
        }).reset_index()

        monthly.columns = ['month', 'orders', 'revenue', 'items_delivered', 'items_missing', 'orders_with_missing']
        monthly['missing_rate'] = (
            monthly['items_missing'] / (monthly['items_delivered'] + monthly['items_missing']) * 100
        )
        monthly['pct_orders_with_missing'] = monthly['orders_with_missing'] / monthly['orders'] * 100

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly['month_name'] = monthly['month'].apply(lambda x: month_names[x-1])

        # Daily trends (day of week)
        daily = orders.groupby(['day_of_week', 'day_of_week_num']).agg({
            'order_id': 'count',
            'order_amount': 'sum',
            'items_delivered': 'sum',
            'items_missing': 'sum'
        }).reset_index().sort_values('day_of_week_num')

        daily.columns = ['day_of_week', 'day_num', 'orders', 'revenue', 'items_delivered', 'items_missing']
        daily['missing_rate'] = (
            daily['items_missing'] / (daily['items_delivered'] + daily['items_missing']) * 100
        )

        # Hourly trends
        hourly = orders.groupby('delivery_hour').agg({
            'order_id': 'count',
            'items_delivered': 'sum',
            'items_missing': 'sum'
        }).reset_index()

        hourly.columns = ['hour', 'orders', 'items_delivered', 'items_missing']
        hourly['missing_rate'] = (
            hourly['items_missing'] / (hourly['items_delivered'] + hourly['items_missing']) * 100
        )

        # Define periods
        def get_period(hour):
            if 6 <= hour < 12:
                return 'Morning'
            elif 12 <= hour < 18:
                return 'Afternoon'
            elif 18 <= hour < 22:
                return 'Evening'
            else:
                return 'Night'

        hourly['period'] = hourly['hour'].apply(get_period)

        result = {
            'monthly': monthly,
            'daily': daily,
            'hourly': hourly
        }

        self._set_cache(cache_key, result)
        return result

    def get_risk_alerts(self, threshold: float = 70.0) -> pd.DataFrame:
        """
        Get high-risk alerts for dashboard.

        Args:
            threshold: Minimum risk score for alerts

        Returns:
            DataFrame with risk alerts
        """
        cache_key = f'risk_alerts_{threshold}'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        driver_summary = self.get_driver_summary()
        customer_summary = self.get_customer_summary()
        regional_summary = self.get_regional_summary()

        alerts = []

        # High-risk drivers
        high_risk_drivers = driver_summary[driver_summary['risk_score'] >= threshold]
        for _, row in high_risk_drivers.iterrows():
            alerts.append({
                'entity_type': 'Driver',
                'entity_id': row['driver_id'],
                'entity_name': row['driver_name'],
                'risk_score': row['risk_score'],
                'risk_category': row['risk_category'],
                'primary_metric': f"Missing rate: {row['missing_rate']:.2f}%",
                'secondary_metric': f"Orders with issues: {row['orders_with_missing']:.0f}",
                'recommendation': 'Review delivery patterns and consider audit'
            })

        # High-risk customers
        high_risk_customers = customer_summary[customer_summary['risk_score'] >= threshold]
        for _, row in high_risk_customers.iterrows():
            alerts.append({
                'entity_type': 'Customer',
                'entity_id': row['customer_id'],
                'entity_name': row['customer_name'],
                'risk_score': row['risk_score'],
                'risk_category': row['risk_category'],
                'primary_metric': f"Claim rate: {row['claim_rate']:.2f}%",
                'secondary_metric': f"Orders with claims: {row['orders_with_claims']:.0f}",
                'recommendation': 'Verify claims and consider enhanced verification'
            })

        # High-risk regions
        overall_missing_rate = regional_summary['missing_rate'].mean()
        high_risk_regions = regional_summary[regional_summary['missing_rate'] > overall_missing_rate * 1.2]
        for _, row in high_risk_regions.iterrows():
            alerts.append({
                'entity_type': 'Region',
                'entity_id': row['region'],
                'entity_name': row['region'],
                'risk_score': row['missing_rate'],
                'risk_category': 'High' if row['missing_rate'] > overall_missing_rate * 1.5 else 'Medium',
                'primary_metric': f"Missing rate: {row['missing_rate']:.2f}%",
                'secondary_metric': f"Items missing: {row['items_missing']:.0f}",
                'recommendation': 'Investigate regional patterns and driver assignments'
            })

        result = pd.DataFrame(alerts)
        if len(result) > 0:
            result = result.sort_values('risk_score', ascending=False)

        self._set_cache(cache_key, result)
        return result

    def get_risk_distribution(self) -> Dict:
        """
        Get risk distribution for drivers and customers.

        Returns:
            Dictionary with risk distribution data
        """
        cache_key = 'risk_distribution'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        driver_summary = self.get_driver_summary()
        customer_summary = self.get_customer_summary()

        driver_risk_dist = driver_summary['risk_category'].value_counts().to_dict()
        customer_risk_dist = customer_summary['risk_category'].value_counts().to_dict()

        result = {
            'driver_risk_distribution': {
                'Low': int(driver_risk_dist.get('Low', 0)),
                'Medium': int(driver_risk_dist.get('Medium', 0)),
                'High': int(driver_risk_dist.get('High', 0)),
                'Critical': int(driver_risk_dist.get('Critical', 0))
            },
            'customer_risk_distribution': {
                'Low': int(customer_risk_dist.get('Low', 0)),
                'Medium': int(customer_risk_dist.get('Medium', 0)),
                'High': int(customer_risk_dist.get('High', 0)),
                'Critical': int(customer_risk_dist.get('Critical', 0))
            }
        }

        self._set_cache(cache_key, result)
        return result

    def get_top_suspicious(self, n: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Get top suspicious entities.

        Args:
            n: Number of entities to return

        Returns:
            Dictionary with top suspicious drivers and customers
        """
        cache_key = f'top_suspicious_{n}'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        driver_summary = self.get_driver_summary()
        customer_summary = self.get_customer_summary()

        top_drivers = driver_summary.nlargest(n, 'risk_score')[[
            'driver_id', 'driver_name', 'age', 'orders_completed',
            'missing_rate', 'pct_orders_with_missing', 'risk_score', 'risk_category'
        ]]

        top_customers = customer_summary.nlargest(n, 'risk_score')[[
            'customer_id', 'customer_name', 'customer_age', 'total_orders',
            'claim_rate', 'pct_orders_with_claims', 'risk_score', 'risk_category'
        ]]

        result = {
            'top_suspicious_drivers': top_drivers,
            'top_suspicious_customers': top_customers
        }

        self._set_cache(cache_key, result)
        return result

    def get_product_summary(self) -> pd.DataFrame:
        """
        Get product analysis summary.

        Returns:
            DataFrame with product analysis
        """
        cache_key = 'product_summary'
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        missing_items = load_missing_items()
        products = load_products()

        # Count missing reports per product
        product_missing = missing_items.groupby('product_id').agg({
            'missing_item_id': 'count',
            'order_id': 'nunique'
        }).reset_index()

        product_missing.columns = ['product_id', 'times_reported_missing', 'orders_affected']

        # Merge with product info
        product_analysis = products.merge(product_missing, on='product_id', how='left')
        product_analysis['times_reported_missing'] = product_analysis['times_reported_missing'].fillna(0).astype(int)
        product_analysis['orders_affected'] = product_analysis['orders_affected'].fillna(0).astype(int)
        product_analysis['estimated_loss'] = product_analysis['times_reported_missing'] * product_analysis['price']

        result = product_analysis.sort_values('times_reported_missing', ascending=False)
        self._set_cache(cache_key, result)
        return result


# Convenience function for creating a cache instance
def create_dashboard_cache(ttl_minutes: int = 15) -> DashboardCache:
    """
    Create a new DashboardCache instance.

    Args:
        ttl_minutes: Cache time-to-live in minutes

    Returns:
        DashboardCache instance
    """
    return DashboardCache(ttl_minutes=ttl_minutes)


# Module-level cache instance for simple usage
_default_cache: Optional[DashboardCache] = None


def get_default_cache(ttl_minutes: int = 15) -> DashboardCache:
    """
    Get or create the default cache instance.

    Args:
        ttl_minutes: Cache time-to-live in minutes (only used if creating new cache)

    Returns:
        Default DashboardCache instance
    """
    global _default_cache
    if _default_cache is None:
        _default_cache = DashboardCache(ttl_minutes=ttl_minutes)
    return _default_cache


if __name__ == "__main__":
    # Test the cache module
    print("Testing DashboardCache...")

    cache = DashboardCache(ttl_minutes=15)

    print("\n1. Testing get_overview_metrics()...")
    metrics = cache.get_overview_metrics()
    print(f"   Total Orders: {metrics['total_orders']:,}")
    print(f"   Total Revenue: ${metrics['total_revenue']:,.2f}")

    print("\n2. Testing get_driver_summary()...")
    drivers = cache.get_driver_summary()
    print(f"   Drivers: {len(drivers)}")

    print("\n3. Testing get_customer_summary()...")
    customers = cache.get_customer_summary()
    print(f"   Customers: {len(customers)}")

    print("\n4. Testing cache info...")
    info = cache.get_cache_info()
    print(f"   Cached keys: {info['cached_keys']}")

    print("\nDashboardCache test complete!")
