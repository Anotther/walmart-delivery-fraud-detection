"""
Reusable filter components for the dashboard.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Tuple


def date_range_filter(
    df: pd.DataFrame,
    date_column: str = "order_date",
    key_prefix: str = ""
) -> Tuple[date, date]:
    """
    Create a date range filter.

    Args:
        df: DataFrame with date column
        date_column: Name of the date column
        key_prefix: Prefix for widget keys

    Returns:
        Tuple of (start_date, end_date)
    """
    df[date_column] = pd.to_datetime(df[date_column])

    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_end_date"
        )

    return start_date, end_date


def region_filter(
    df: pd.DataFrame,
    region_column: str = "region",
    key_prefix: str = ""
) -> List[str]:
    """
    Create a region multi-select filter.

    Args:
        df: DataFrame with region column
        region_column: Name of the region column
        key_prefix: Prefix for widget keys

    Returns:
        List of selected regions
    """
    regions = sorted(df[region_column].unique().tolist())

    selected = st.multiselect(
        "Select Regions",
        options=regions,
        default=regions,
        key=f"{key_prefix}_regions"
    )

    return selected if selected else regions


def numeric_range_filter(
    df: pd.DataFrame,
    column: str,
    label: str,
    key_prefix: str = ""
) -> Tuple[float, float]:
    """
    Create a numeric range slider filter.

    Args:
        df: DataFrame
        column: Column name
        label: Display label
        key_prefix: Prefix for widget keys

    Returns:
        Tuple of (min_value, max_value)
    """
    min_val = float(df[column].min())
    max_val = float(df[column].max())

    values = st.slider(
        label,
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val),
        key=f"{key_prefix}_{column}_range"
    )

    return values


def category_filter(
    df: pd.DataFrame,
    column: str,
    label: str,
    key_prefix: str = "",
    default_all: bool = True
) -> List[str]:
    """
    Create a category multi-select filter.

    Args:
        df: DataFrame
        column: Column name
        label: Display label
        key_prefix: Prefix for widget keys
        default_all: Select all by default

    Returns:
        List of selected categories
    """
    categories = sorted(df[column].dropna().unique().tolist())

    default = categories if default_all else []

    selected = st.multiselect(
        label,
        options=categories,
        default=default,
        key=f"{key_prefix}_{column}"
    )

    return selected if selected else categories


def search_filter(
    label: str = "Search",
    key_prefix: str = ""
) -> str:
    """
    Create a text search filter.

    Args:
        label: Display label
        key_prefix: Prefix for widget keys

    Returns:
        Search query string
    """
    return st.text_input(
        label,
        value="",
        key=f"{key_prefix}_search"
    )


def risk_level_filter(
    key_prefix: str = ""
) -> List[str]:
    """
    Create a risk level filter.

    Args:
        key_prefix: Prefix for widget keys

    Returns:
        List of selected risk levels
    """
    levels = ["Low", "Medium", "High", "Critical"]

    selected = st.multiselect(
        "Risk Level",
        options=levels,
        default=levels,
        key=f"{key_prefix}_risk_level"
    )

    return selected if selected else levels


def apply_filters(
    df: pd.DataFrame,
    date_range: Optional[Tuple[date, date]] = None,
    date_column: str = "order_date",
    regions: Optional[List[str]] = None,
    region_column: str = "region",
    search_query: Optional[str] = None,
    search_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Apply multiple filters to a DataFrame.

    Args:
        df: Input DataFrame
        date_range: Tuple of (start_date, end_date)
        date_column: Name of date column
        regions: List of regions to include
        region_column: Name of region column
        search_query: Text search query
        search_columns: Columns to search in

    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()

    # Date filter
    if date_range and date_column in filtered.columns:
        filtered[date_column] = pd.to_datetime(filtered[date_column])
        start, end = date_range
        filtered = filtered[
            (filtered[date_column].dt.date >= start) &
            (filtered[date_column].dt.date <= end)
        ]

    # Region filter
    if regions and region_column in filtered.columns:
        filtered = filtered[filtered[region_column].isin(regions)]

    # Search filter
    if search_query and search_columns:
        mask = pd.Series([False] * len(filtered))
        for col in search_columns:
            if col in filtered.columns:
                mask |= filtered[col].astype(str).str.contains(
                    search_query, case=False, na=False
                )
        filtered = filtered[mask]

    return filtered


def create_filter_sidebar(
    df: pd.DataFrame,
    key_prefix: str = ""
) -> dict:
    """
    Create a complete filter sidebar.

    Args:
        df: DataFrame to filter
        key_prefix: Prefix for widget keys

    Returns:
        Dictionary with filter values
    """
    st.sidebar.markdown("### Filters")

    filters = {}

    # Date range
    if "order_date" in df.columns:
        st.sidebar.markdown("#### Date Range")
        start, end = date_range_filter(df, key_prefix=key_prefix)
        filters["date_range"] = (start, end)

    # Regions
    if "region" in df.columns:
        st.sidebar.markdown("#### Regions")
        filters["regions"] = region_filter(df, key_prefix=key_prefix)

    # Risk levels (if available)
    if "risk_category" in df.columns:
        st.sidebar.markdown("#### Risk Level")
        filters["risk_levels"] = risk_level_filter(key_prefix=key_prefix)

    # Search
    st.sidebar.markdown("#### Search")
    filters["search"] = search_filter(key_prefix=key_prefix)

    return filters
