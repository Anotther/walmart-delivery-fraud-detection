"""
Validation script for the Overview page data layer.

Tests that all data returned by the data source abstraction and DashboardCache
matches the exact structure expected by dashboard/pages/1_Overview.py.

Run from the project root:
    python scripts/validate_overview_page.py

Exit code 0 = all checks passed
Exit code 1 = one or more issues found
"""

import sys
import traceback
from pathlib import Path

# Ensure project root is on sys.path so src.* imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

_issues: list[dict] = []
_warnings: list[dict] = []


def _record_issue(check: str, detail: str, exception: Exception | None = None) -> None:
    entry = {"check": check, "detail": detail}
    if exception:
        entry["exception"] = str(exception)
    _issues.append(entry)
    print(f"  {FAIL} {check}")
    print(f"       {detail}")
    if exception:
        print(f"       Exception: {exception}")


def _record_warning(check: str, detail: str) -> None:
    _warnings.append({"check": check, "detail": detail})
    print(f"  {WARN} {check}")
    print(f"       {detail}")


def _ok(check: str) -> None:
    print(f"  {PASS} {check}")


# ---------------------------------------------------------------------------
# Section 1 – Raw data source loads
# ---------------------------------------------------------------------------

def test_data_source_loads() -> dict:
    """Load all five raw tables and verify expected columns exist."""
    print("\n--- Section 1: Raw DataSource Loads ---")

    from src.data_source.csv_source import CSVDataSource
    ds = CSVDataSource()

    results = {}

    # Orders
    try:
        orders = ds.load_orders()
        results["orders"] = orders
        required = {"order_id", "order_date", "order_amount", "region",
                    "items_delivered", "items_missing", "delivery_hour",
                    "driver_id", "customer_id"}
        missing_cols = required - set(orders.columns)
        if missing_cols:
            _record_issue(
                "orders - required columns",
                f"Missing columns: {sorted(missing_cols)}"
            )
        else:
            _ok(f"orders loaded ({len(orders):,} rows, all required columns present)")
            # Check for NaN in critical numeric columns
            for col in ("items_delivered", "items_missing", "order_amount"):
                n_nan = orders[col].isna().sum()
                if n_nan > 0:
                    _record_warning(
                        f"orders['{col}'] NaN check",
                        f"{n_nan} NaN values found – may cause arithmetic errors"
                    )
    except Exception as exc:
        _record_issue("orders load", "Exception during load_orders()", exc)

    # Drivers
    try:
        drivers = ds.load_drivers()
        results["drivers"] = drivers
        required = {"driver_id", "driver_name", "age", "trips"}
        missing_cols = required - set(drivers.columns)
        if missing_cols:
            _record_issue(
                "drivers - required columns",
                f"Missing columns: {sorted(missing_cols)}"
            )
        else:
            _ok(f"drivers loaded ({len(drivers):,} rows, all required columns present)")
    except Exception as exc:
        _record_issue("drivers load", "Exception during load_drivers()", exc)

    # Customers
    try:
        customers = ds.load_customers()
        results["customers"] = customers
        required = {"customer_id", "customer_name", "customer_age"}
        missing_cols = required - set(customers.columns)
        if missing_cols:
            _record_issue(
                "customers - required columns",
                f"Missing columns: {sorted(missing_cols)}"
            )
        else:
            _ok(f"customers loaded ({len(customers):,} rows, all required columns present)")
    except Exception as exc:
        _record_issue("customers load", "Exception during load_customers()", exc)

    # Products
    try:
        products = ds.load_products()
        results["products"] = products
        required = {"product_id", "product_name", "category", "price"}
        missing_cols = required - set(products.columns)
        if missing_cols:
            _record_issue(
                "products - required columns",
                f"Missing columns: {sorted(missing_cols)}"
            )
        else:
            _ok(f"products loaded ({len(products):,} rows, all required columns present)")
    except Exception as exc:
        _record_issue("products load", "Exception during load_products()", exc)

    # Missing items
    try:
        missing = ds.load_missing_items()
        results["missing_items"] = missing
        required = {"missing_item_id", "order_id", "product_id", "item_position"}
        missing_cols = required - set(missing.columns)
        if missing_cols:
            _record_issue(
                "missing_items - required columns",
                f"Missing columns: {sorted(missing_cols)}"
            )
        else:
            _ok(f"missing_items loaded ({len(missing):,} rows, all required columns present)")
    except Exception as exc:
        _record_issue("missing_items load", "Exception during load_missing_items()", exc)

    return results


# ---------------------------------------------------------------------------
# Section 2 – get_overview_metrics() keys vs 1_Overview.py expectations
# ---------------------------------------------------------------------------

def test_overview_metrics(cache) -> dict:
    """
    Verify every key that 1_Overview.py reads from the metrics dict exists
    and has an appropriate type.

    Keys consumed in 1_Overview.py (by line reference):
        Line  65 : metrics['estimated_loss']             (float)
        Line  97 : trends['monthly']                     (handled in section 3)
        Line 114 : metrics['date_range_start']           (str)
        Line 114 : metrics['date_range_end']             (str)
        Line 125 : metrics['total_orders']               (int)
        Line 129 : metrics['date_range_start']           (str)
        Line 129 : metrics['date_range_end']             (str)
        Line 137 : metrics['overall_missing_rate']       (float)
        Line 224 : metrics['orders_with_missing']        (int)
        Line 225 : metrics['pct_orders_with_missing']    (float)
        Line 234 : metrics['total_orders']               (int – duplicate read)
    """
    print("\n--- Section 2: get_overview_metrics() ---")

    try:
        metrics = cache.get_overview_metrics()
    except Exception as exc:
        _record_issue("get_overview_metrics()", "Exception during call", exc)
        return {}

    if not isinstance(metrics, dict):
        _record_issue("get_overview_metrics() type", f"Expected dict, got {type(metrics)}")
        return {}

    # Map: key -> (expected_python_type, description_from_page)
    EXPECTED_KEYS = {
        "total_orders":            (int,   "line 125, 234 – order count KPI"),
        "overall_missing_rate":    (float, "line 137 – missing item rate KPI"),
        "orders_with_missing":     (int,   "line 224 – flagged orders"),
        "pct_orders_with_missing": (float, "line 225 – flagged orders pct"),
        "estimated_loss":          (float, "line 65 – business impact calculation"),
        "date_range_start":        (str,   "lines 114, 129 – caption and tooltip"),
        "date_range_end":          (str,   "lines 114, 129 – caption and tooltip"),
    }

    all_ok = True
    for key, (expected_type, description) in EXPECTED_KEYS.items():
        if key not in metrics:
            _record_issue(
                f"overview_metrics['{key}']",
                f"Key missing – used at {description}"
            )
            all_ok = False
        else:
            value = metrics[key]
            if value is None:
                _record_issue(
                    f"overview_metrics['{key}'] is None",
                    f"None value will crash arithmetic at {description}"
                )
                all_ok = False
            elif not isinstance(value, expected_type):
                _record_warning(
                    f"overview_metrics['{key}'] type",
                    f"Expected {expected_type.__name__}, got {type(value).__name__} "
                    f"(value={value!r}). Used at {description}"
                )
            else:
                _ok(f"overview_metrics['{key}'] = {value!r}")

    return metrics


# ---------------------------------------------------------------------------
# Section 3 – get_temporal_trends() structure
# ---------------------------------------------------------------------------

def test_temporal_trends(cache) -> dict:
    """
    1_Overview.py expects trends to be a dict with key 'monthly'.
    monthly must be a DataFrame with columns:
        missing_rate, month_name, orders, items_missing
    (lines 83-88, 97, 251-307)
    """
    print("\n--- Section 3: get_temporal_trends() ---")

    try:
        trends = cache.get_temporal_trends()
    except Exception as exc:
        _record_issue("get_temporal_trends()", "Exception during call", exc)
        return {}

    if not isinstance(trends, dict):
        _record_issue("get_temporal_trends() type", f"Expected dict, got {type(trends)}")
        return {}

    # Top-level keys
    for key in ("monthly", "daily", "hourly"):
        if key not in trends:
            _record_issue(f"temporal_trends['{key}']", "Key missing from trends dict")
        else:
            _ok(f"temporal_trends['{key}'] key present ({type(trends[key]).__name__})")

    if "monthly" not in trends:
        return trends

    monthly = trends["monthly"]

    if not isinstance(monthly, pd.DataFrame):
        _record_issue("temporal_trends['monthly'] type",
                      f"Expected DataFrame, got {type(monthly)}")
        return trends

    _ok(f"temporal_trends['monthly'] is a DataFrame with {len(monthly)} rows")

    # Columns accessed in 1_Overview.py
    MONTHLY_REQUIRED = {
        "missing_rate":  "lines 83, 251, 256-258, 267-268, 296 – all trend calculations",
        "month_name":    "lines 259, 268, 302, 303 – axis labels, peak label, hover",
        "orders":        "line 307 – hover_data in plot_line_chart",
        "items_missing": "line 307 – hover_data in plot_line_chart",
    }

    for col, description in MONTHLY_REQUIRED.items():
        if col not in monthly.columns:
            _record_issue(
                f"temporal_trends['monthly']['{col}']",
                f"Column missing – used at {description}"
            )
        else:
            null_count = monthly[col].isna().sum()
            if null_count > 0:
                _record_warning(
                    f"temporal_trends['monthly']['{col}'] NaN check",
                    f"{null_count} NaN values – may cause KeyError/ValueError in trend math"
                )
            else:
                _ok(f"monthly['{col}'] present, no NaN")

    # Edge case: empty monthly DataFrame
    if len(monthly) == 0:
        _record_issue(
            "temporal_trends['monthly'] empty",
            "Empty DataFrame – calculate_trend_delta and plot_line_chart will silently skip "
            "but avg_rate = 0, peak_text = 'N/A', and stat_card values will be misleading"
        )

    return trends


# ---------------------------------------------------------------------------
# Section 4 – get_risk_alerts() structure
# ---------------------------------------------------------------------------

def test_risk_alerts(cache) -> pd.DataFrame:
    """
    1_Overview.py calls cache.get_risk_alerts(threshold=70).
    It then filters by risk_category == 'Critical' and == 'High' (lines 164-165).
    risk_category must exist and be string-like.
    """
    print("\n--- Section 4: get_risk_alerts(threshold=70) ---")

    try:
        alerts = cache.get_risk_alerts(threshold=70)
    except Exception as exc:
        _record_issue("get_risk_alerts(threshold=70)", "Exception during call", exc)
        return pd.DataFrame()

    if not isinstance(alerts, pd.DataFrame):
        _record_issue("get_risk_alerts() type", f"Expected DataFrame, got {type(alerts)}")
        return pd.DataFrame()

    _ok(f"get_risk_alerts() returned DataFrame with {len(alerts)} rows")

    if len(alerts) == 0:
        # Empty DataFrame is handled by the page (len(alerts) > 0 guard), but
        # verify it at least has the right columns so the guard check doesn't KeyError
        _record_warning(
            "get_risk_alerts() empty",
            "No alerts above threshold=70. The page handles this with 'if len(alerts) > 0' "
            "but confirm risk_category column exists even on empty DFs."
        )
        # Check columns on empty DF
        if "risk_category" not in alerts.columns:
            _record_issue(
                "get_risk_alerts() empty - missing risk_category column",
                "When DataFrame is empty, filtering alerts[alerts['risk_category'] == 'Critical'] "
                "will raise KeyError. Column must be present even for empty result."
            )
        return alerts

    # Non-empty: verify required columns
    REQUIRED_COLS = {
        "risk_category": "lines 164-165 – filter by 'Critical' and 'High'",
        "risk_score":    "line 847 – sorted by risk_score",
        "entity_type":   "structural column",
        "entity_id":     "structural column",
        "entity_name":   "structural column",
    }
    for col, description in REQUIRED_COLS.items():
        if col not in alerts.columns:
            _record_issue(
                f"alerts['{col}']",
                f"Column missing – used at {description}"
            )
        else:
            _ok(f"alerts['{col}'] present")

    # Check risk_category values are valid strings
    if "risk_category" in alerts.columns:
        unique_cats = alerts["risk_category"].unique()
        valid_cats = {"Critical", "High", "Medium", "Low"}
        unexpected = set(str(c) for c in unique_cats) - valid_cats
        if unexpected:
            _record_warning(
                "alerts['risk_category'] unexpected values",
                f"Found: {unexpected}. Page filters for 'Critical' and 'High' only."
            )
        else:
            _ok(f"alerts['risk_category'] values OK: {sorted(str(c) for c in unique_cats)}")

    return alerts


# ---------------------------------------------------------------------------
# Section 5 – get_risk_distribution() structure
# ---------------------------------------------------------------------------

def test_risk_distribution(cache) -> dict:
    """
    1_Overview.py reads:
        risk_dist['driver_risk_distribution']   (lines 186-188)
        risk_dist['customer_risk_distribution'] (lines 204-206)
    Both must be dicts with keys 'Critical', 'High', 'Medium'.
    """
    print("\n--- Section 5: get_risk_distribution() ---")

    try:
        risk_dist = cache.get_risk_distribution()
    except Exception as exc:
        _record_issue("get_risk_distribution()", "Exception during call", exc)
        return {}

    if not isinstance(risk_dist, dict):
        _record_issue("get_risk_distribution() type",
                      f"Expected dict, got {type(risk_dist)}")
        return {}

    for top_key in ("driver_risk_distribution", "customer_risk_distribution"):
        if top_key not in risk_dist:
            _record_issue(
                f"risk_dist['{top_key}']",
                f"Top-level key missing"
            )
            continue

        sub = risk_dist[top_key]
        if not isinstance(sub, dict):
            _record_issue(
                f"risk_dist['{top_key}'] type",
                f"Expected dict, got {type(sub)}"
            )
            continue

        for cat_key in ("Critical", "High", "Medium"):
            if cat_key not in sub:
                _record_issue(
                    f"risk_dist['{top_key}']['{cat_key}']",
                    f"Key missing – page reads .get('{cat_key}', 0) so this won't crash "
                    f"but the displayed count will always be 0"
                )
            else:
                val = sub[cat_key]
                if not isinstance(val, int):
                    _record_warning(
                        f"risk_dist['{top_key}']['{cat_key}'] type",
                        f"Expected int, got {type(val).__name__} (value={val!r})"
                    )
                else:
                    _ok(f"risk_dist['{top_key}']['{cat_key}'] = {val}")

    return risk_dist


# ---------------------------------------------------------------------------
# Section 6 – get_regional_summary() columns
# ---------------------------------------------------------------------------

def test_regional_summary(cache) -> pd.DataFrame:
    """
    1_Overview.py accesses these regional columns (lines 320-395):
        missing_rate, total_orders, region, items_missing
    """
    print("\n--- Section 6: get_regional_summary() ---")

    try:
        regional = cache.get_regional_summary()
    except Exception as exc:
        _record_issue("get_regional_summary()", "Exception during call", exc)
        return pd.DataFrame()

    if not isinstance(regional, pd.DataFrame):
        _record_issue("get_regional_summary() type",
                      f"Expected DataFrame, got {type(regional)}")
        return pd.DataFrame()

    _ok(f"get_regional_summary() returned DataFrame with {len(regional)} rows")

    if len(regional) == 0:
        _record_warning(
            "get_regional_summary() empty",
            "Empty DataFrame – the page has an 'if not regional.empty' guard but "
            "regional charts will not render"
        )
        return regional

    REQUIRED_COLS = {
        "missing_rate":  "lines 320, 321, 323-328 – sorting and risk level calculation",
        "total_orders":  "line 353 – row display in regional breakdown",
        "region":        "line 350, 362 – row display and bar chart x-axis",
        "items_missing": "line 375 – custom_data for bar chart hover template",
    }

    for col, description in REQUIRED_COLS.items():
        if col not in regional.columns:
            _record_issue(
                f"regional['{col}']",
                f"Column missing – used at {description}"
            )
        else:
            null_count = regional[col].isna().sum()
            if null_count > 0:
                _record_warning(
                    f"regional['{col}'] NaN check",
                    f"{null_count} NaN values found"
                )
            else:
                _ok(f"regional['{col}'] present, no NaN")

    return regional


# ---------------------------------------------------------------------------
# Section 7 – get_page_data('overview') key propagation
# ---------------------------------------------------------------------------

def test_page_data_overview(cache) -> None:
    """
    DashboardCache.get_page_data('overview') stores results under keys derived
    by stripping 'get_' prefix from method names.

    Method                  -> stored key
    get_overview_metrics    -> overview_metrics
    get_temporal_trends     -> temporal_trends
    get_risk_alerts         -> risk_alerts
    get_risk_distribution   -> risk_distribution
    get_top_suspicious      -> top_suspicious

    1_Overview.py reads from page_data at lines 48-54.
    """
    print("\n--- Section 7: get_page_data('overview') key propagation ---")

    try:
        page_data = cache.get_page_data("overview")
    except Exception as exc:
        _record_issue("get_page_data('overview')", "Exception during call", exc)
        return

    if not isinstance(page_data, dict):
        _record_issue("get_page_data('overview') type",
                      f"Expected dict, got {type(page_data)}")
        return

    EXPECTED_PAGE_KEYS = {
        "overview_metrics": "line 48 – page_data['overview_metrics']",
        "temporal_trends":  "line 49 – page_data['temporal_trends']",
        "risk_distribution":"line 53 – page_data['risk_distribution']",
        "top_suspicious":   "line 54 – page_data['top_suspicious']",
    }

    for key, description in EXPECTED_PAGE_KEYS.items():
        if key not in page_data:
            # Check if an error key was set instead
            error_key = f"get_{key}_error"
            if error_key in page_data:
                _record_issue(
                    f"page_data['{key}'] missing – error recorded",
                    f"get_page_data silently caught exception and stored it under "
                    f"'{error_key}': {page_data[error_key]}. "
                    f"Page accesses {description} but will get KeyError."
                )
            else:
                _record_issue(
                    f"page_data['{key}']",
                    f"Key missing and no error key found. Used at {description}"
                )
        else:
            val = page_data[key]
            if val is None:
                _record_issue(
                    f"page_data['{key}'] is None",
                    f"None value at {description} will crash on attribute access"
                )
            else:
                _ok(f"page_data['{key}'] present ({type(val).__name__})")

    # Check for any silently-swallowed errors from the lazy-load loop
    error_keys = [k for k in page_data if k.endswith("_error")]
    if error_keys:
        for ek in error_keys:
            _record_issue(
                f"get_page_data silently swallowed error: {ek}",
                f"Error message: {page_data[ek]}"
            )
    else:
        _ok("No silent errors in get_page_data('overview') loop")


# ---------------------------------------------------------------------------
# Section 8 – Type correctness of delivery_hour after transformation
# ---------------------------------------------------------------------------

def test_delivery_hour_transformation(cache) -> None:
    """
    _compute_orders_with_features() parses delivery_hour into an integer hour.
    It is later used in groupby('delivery_hour') and pd.cut(...) calls.
    If it remains as datetime.time objects, the groupby and cut will still work
    but the hour bucketing in get_hypothesis_results() uses pd.cut with integer
    bins [-1, 6, 12, 18, 24] – this would fail if delivery_hour is time type.
    """
    print("\n--- Section 8: delivery_hour type after feature computation ---")

    try:
        orders = cache.get_orders_with_features()
    except Exception as exc:
        _record_issue("get_orders_with_features()", "Exception during call", exc)
        return

    if "delivery_hour" not in orders.columns:
        _record_issue("orders['delivery_hour']", "Column missing after feature computation")
        return

    dtype = orders["delivery_hour"].dtype
    sample_val = orders["delivery_hour"].iloc[0] if len(orders) > 0 else None

    if pd.api.types.is_integer_dtype(dtype):
        _ok(f"delivery_hour dtype is integer ({dtype}), sample value: {sample_val}")
    elif pd.api.types.is_float_dtype(dtype):
        _record_warning(
            "delivery_hour dtype is float",
            f"Expected int, got {dtype}. pd.cut with integer bins may still work "
            f"but groupby will produce float keys instead of int."
        )
    else:
        _record_issue(
            "delivery_hour dtype",
            f"Expected integer, got {dtype} (sample: {sample_val!r}). "
            f"pd.cut in get_hypothesis_results() uses integer bins [-1,6,12,18,24] "
            f"and will raise TypeError if delivery_hour is still datetime.time."
        )


# ---------------------------------------------------------------------------
# Section 9 – order_date type after transformation
# ---------------------------------------------------------------------------

def test_order_date_type(cache) -> None:
    """
    get_overview_metrics() calls orders['order_date'].min().date() (line 494).
    This requires order_date to be a Timestamp/datetime, not a raw date string
    or datetime.date object (which doesn't have a .date() method – it IS a date).
    Also checks: _compute_orders_with_features calls pd.to_datetime(orders['order_date']).
    """
    print("\n--- Section 9: order_date type ---")

    try:
        orders = cache.get_orders_with_features()
    except Exception as exc:
        _record_issue("get_orders_with_features() for date check", "Exception", exc)
        return

    if "order_date" not in orders.columns:
        _record_issue("orders['order_date']", "Column missing")
        return

    dtype = orders["order_date"].dtype
    sample = orders["order_date"].iloc[0] if len(orders) > 0 else None

    if hasattr(sample, "year") and hasattr(sample, "month"):
        # Covers both datetime.date and pd.Timestamp
        import datetime as _dt
        if isinstance(sample, pd.Timestamp):
            _ok(f"order_date is pd.Timestamp ({dtype}), .date() method available")
        elif isinstance(sample, _dt.date):
            # datetime.date objects don't have .date() – calling it will AttributeError
            _record_issue(
                "order_date is datetime.date, not pd.Timestamp",
                f"orders['order_date'].min() returns datetime.date which has no .date() method. "
                f"get_overview_metrics() calls .min().date() at line 494 – will raise "
                f"AttributeError: 'datetime.date' object has no attribute 'date'. "
                f"Fix: convert with pd.to_datetime() before calling .date()."
            )
        else:
            _record_warning(
                "order_date type unknown",
                f"dtype={dtype}, sample type={type(sample).__name__}"
            )
    else:
        _record_issue(
            "order_date is not a date-like object",
            f"dtype={dtype}, sample={sample!r}"
        )


# ---------------------------------------------------------------------------
# Section 10 – risk_category Categorical type in filter operations
# ---------------------------------------------------------------------------

def test_risk_category_filter(cache) -> None:
    """
    get_risk_distribution() calls driver_summary['risk_category'].value_counts().to_dict().
    risk_category is created with pd.cut(..., labels=[...]) which returns a Categorical.
    Categorical .to_dict() keys are the label strings, which is fine.

    However, in get_risk_alerts(), the comparison:
        driver_summary[driver_summary['risk_score'] >= threshold]
    and then row['risk_category'] is accessed directly (line 809 in data_cache.py).

    If risk_category is Categorical, row['risk_category'] returns a category scalar,
    and when appended to the alerts list it becomes a Categorical scalar.
    Then in 1_Overview.py line 164:
        alerts[alerts['risk_category'] == 'Critical']
    This comparison works with Categorical but only if 'Critical' is a valid category.
    Let us verify the actual stored type.
    """
    print("\n--- Section 10: risk_category Categorical type compatibility ---")

    try:
        drivers = cache.get_driver_summary()
    except Exception as exc:
        _record_issue("get_driver_summary() for category check", "Exception", exc)
        return

    if "risk_category" not in drivers.columns:
        _record_issue("driver_summary['risk_category']", "Column missing")
        return

    dtype = drivers["risk_category"].dtype
    _ok(f"driver_summary['risk_category'] dtype: {dtype}")

    # Verify that filtering works correctly (mimics what 1_Overview.py does)
    try:
        alerts = cache.get_risk_alerts(threshold=70)
        if len(alerts) > 0 and "risk_category" in alerts.columns:
            critical_count = len(alerts[alerts["risk_category"] == "Critical"])
            high_count = len(alerts[alerts["risk_category"] == "High"])
            _ok(
                f"alerts filter 'Critical'={critical_count}, 'High'={high_count} "
                f"– string equality on risk_category works"
            )
        else:
            _ok("alerts empty or missing risk_category – filter test skipped")
    except Exception as exc:
        _record_issue(
            "alerts['risk_category'] == 'Critical' filter",
            "String equality comparison on risk_category raised an exception",
            exc
        )


# ---------------------------------------------------------------------------
# Section 11 – calculate_business_impact() key dependency
# ---------------------------------------------------------------------------

def test_business_impact_key(cache) -> None:
    """
    calculate_business_impact() in 1_Overview.py reads metrics['estimated_loss']
    at line 65.  Verify it is a float and non-None.
    """
    print("\n--- Section 11: calculate_business_impact() dependency ---")

    try:
        metrics = cache.get_overview_metrics()
    except Exception as exc:
        _record_issue("get_overview_metrics() for business impact", "Exception", exc)
        return

    if "estimated_loss" not in metrics:
        _record_issue(
            "metrics['estimated_loss'] missing",
            "calculate_business_impact() at line 65 reads this key and will raise KeyError"
        )
        return

    val = metrics["estimated_loss"]
    if val is None:
        _record_issue(
            "metrics['estimated_loss'] is None",
            "Line 65: estimated_annual_loss = metrics['estimated_loss'] * 12 "
            "will raise TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'"
        )
        return

    if not isinstance(val, (int, float)):
        _record_issue(
            "metrics['estimated_loss'] type",
            f"Expected numeric, got {type(val).__name__} ({val!r}). "
            f"Multiplication at line 65 will raise TypeError."
        )
        return

    annual = val * 12
    savings = annual * 0.25
    _ok(f"estimated_loss={val:.2f} -> projected_annual={annual:.2f}, savings={savings:.2f}")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("  Walmart Fraud Detection – Overview Page Validation")
    print("=" * 70)

    # Build cache with CSV source (no DB needed)
    from src.data_source.csv_source import CSVDataSource
    from src.dashboard.data_cache import DashboardCache
    from src.database.manager import get_db_manager

    csv_source = CSVDataSource()
    db_manager = get_db_manager()
    cache = DashboardCache(ttl_minutes=0, db_manager=db_manager, data_source=csv_source)

    # Run all test sections
    test_data_source_loads()
    metrics = test_overview_metrics(cache)
    trends = test_temporal_trends(cache)
    alerts = test_risk_alerts(cache)
    risk_dist = test_risk_distribution(cache)
    test_regional_summary(cache)
    test_page_data_overview(cache)
    test_delivery_hour_transformation(cache)
    test_order_date_type(cache)
    test_risk_category_filter(cache)
    test_business_impact_key(cache)

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Issues (FAIL): {len(_issues)}")
    print(f"  Warnings:      {len(_warnings)}")

    if _issues:
        print("\n  ISSUES REQUIRING FIX:")
        for i, issue in enumerate(_issues, 1):
            print(f"\n  [{i}] Check  : {issue['check']}")
            print(f"      Detail : {issue['detail']}")
            if "exception" in issue:
                print(f"      Exception: {issue['exception']}")

    if _warnings:
        print("\n  WARNINGS (should be reviewed):")
        for i, warn in enumerate(_warnings, 1):
            print(f"\n  [{i}] Check  : {warn['check']}")
            print(f"      Detail : {warn['detail']}")

    if not _issues and not _warnings:
        print("\n  All checks passed – Overview page data layer is consistent.")

    print("=" * 70)
    return 1 if _issues else 0


if __name__ == "__main__":
    sys.exit(main())
