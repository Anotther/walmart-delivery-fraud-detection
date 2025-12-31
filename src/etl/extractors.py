"""
Data extractors for reading CSV files.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

from src.config.settings import DATA_FILES, DATA_DIR


def extract_orders(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Extract orders data from CSV.

    Args:
        filepath: Optional custom path. Uses default if not provided.

    Returns:
        DataFrame with orders data.
    """
    path = filepath or DATA_FILES["orders"]
    df = pd.read_csv(path)
    return df


def extract_customers(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Extract customers data from CSV.

    Args:
        filepath: Optional custom path. Uses default if not provided.

    Returns:
        DataFrame with customers data.
    """
    path = filepath or DATA_FILES["customers"]
    df = pd.read_csv(path)
    return df


def extract_drivers(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Extract drivers data from CSV.

    Args:
        filepath: Optional custom path. Uses default if not provided.

    Returns:
        DataFrame with drivers data.
    """
    path = filepath or DATA_FILES["drivers"]
    df = pd.read_csv(path)
    return df


def extract_products(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Extract products data from CSV.

    Args:
        filepath: Optional custom path. Uses default if not provided.

    Returns:
        DataFrame with products data.
    """
    path = filepath or DATA_FILES["products"]
    df = pd.read_csv(path)
    return df


def extract_missing_items(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Extract missing items data from CSV.

    Args:
        filepath: Optional custom path. Uses default if not provided.

    Returns:
        DataFrame with missing items data.
    """
    path = filepath or DATA_FILES["missing_items"]
    df = pd.read_csv(path)
    return df


def extract_all() -> Dict[str, pd.DataFrame]:
    """
    Extract all datasets from CSV files.

    Returns:
        Dictionary with all DataFrames keyed by name.
    """
    return {
        "orders": extract_orders(),
        "customers": extract_customers(),
        "drivers": extract_drivers(),
        "products": extract_products(),
        "missing_items": extract_missing_items(),
    }


def get_data_info() -> Dict[str, Dict]:
    """
    Get basic information about all data files.

    Returns:
        Dictionary with file info (exists, size, rows estimate).
    """
    info = {}
    for name, path in DATA_FILES.items():
        path = Path(path)
        if path.exists():
            df = pd.read_csv(path, nrows=0)
            with open(path) as f:
                row_count = sum(1 for _ in f) - 1
            info[name] = {
                "exists": True,
                "path": str(path),
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "columns": list(df.columns),
                "row_count": row_count,
            }
        else:
            info[name] = {"exists": False, "path": str(path)}
    return info
