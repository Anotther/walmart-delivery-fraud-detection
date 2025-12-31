"""
Table components for the dashboard.
"""
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Callable


def styled_dataframe(
    df: pd.DataFrame,
    height: Optional[int] = None,
    hide_index: bool = True
):
    """
    Display a styled dataframe.

    Args:
        df: DataFrame to display
        height: Optional fixed height
        hide_index: Whether to hide the index
    """
    st.dataframe(
        df,
        height=height,
        hide_index=hide_index,
        use_container_width=True
    )


def sortable_table(
    df: pd.DataFrame,
    default_sort: str,
    ascending: bool = True,
    key_prefix: str = ""
):
    """
    Create a sortable table.

    Args:
        df: DataFrame to display
        default_sort: Default sort column
        ascending: Default sort order
        key_prefix: Key prefix for widgets
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        sort_col = st.selectbox(
            "Sort by",
            options=df.columns.tolist(),
            index=df.columns.tolist().index(default_sort) if default_sort in df.columns else 0,
            key=f"{key_prefix}_sort_col"
        )

    with col2:
        sort_order = st.selectbox(
            "Order",
            options=["Ascending", "Descending"],
            index=0 if ascending else 1,
            key=f"{key_prefix}_sort_order"
        )

    sorted_df = df.sort_values(
        by=sort_col,
        ascending=(sort_order == "Ascending")
    )

    styled_dataframe(sorted_df)


def paginated_table(
    df: pd.DataFrame,
    page_size: int = 20,
    key_prefix: str = ""
):
    """
    Create a paginated table.

    Args:
        df: DataFrame to display
        page_size: Rows per page
        key_prefix: Key prefix for widgets
    """
    total_rows = len(df)
    total_pages = (total_rows - 1) // page_size + 1

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        page = st.number_input(
            f"Page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            key=f"{key_prefix}_page"
        )

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    st.markdown(f"Showing {start_idx + 1}-{end_idx} of {total_rows} rows")

    styled_dataframe(df.iloc[start_idx:end_idx])


def highlight_table(
    df: pd.DataFrame,
    highlight_column: str,
    thresholds: Dict[str, float],
    colors: Optional[Dict[str, str]] = None
):
    """
    Create a table with conditional highlighting.

    Args:
        df: DataFrame to display
        highlight_column: Column to base highlighting on
        thresholds: Dict with 'low', 'medium', 'high' thresholds
        colors: Optional custom colors
    """
    if colors is None:
        colors = {
            "low": "background-color: #d4edda",
            "medium": "background-color: #fff3cd",
            "high": "background-color: #f8d7da"
        }

    def highlight(row):
        val = row[highlight_column]
        if val < thresholds.get("low", 25):
            return [colors["low"]] * len(row)
        elif val < thresholds.get("medium", 50):
            return [colors["medium"]] * len(row)
        else:
            return [colors["high"]] * len(row)

    styled = df.style.apply(highlight, axis=1)
    st.dataframe(styled, use_container_width=True)


def summary_table(
    df: pd.DataFrame,
    group_by: str,
    agg_columns: Dict[str, str],
    sort_by: Optional[str] = None,
    ascending: bool = False
):
    """
    Create an aggregated summary table.

    Args:
        df: DataFrame
        group_by: Column to group by
        agg_columns: Dict of {column: aggregation_function}
        sort_by: Column to sort by
        ascending: Sort order
    """
    summary = df.groupby(group_by).agg(agg_columns).reset_index()

    # Flatten column names if multi-level
    if isinstance(summary.columns, pd.MultiIndex):
        summary.columns = ["_".join(col).strip("_") for col in summary.columns]

    if sort_by:
        summary = summary.sort_values(by=sort_by, ascending=ascending)

    styled_dataframe(summary)


def detail_expander(
    df: pd.DataFrame,
    id_column: str,
    display_columns: List[str],
    detail_columns: List[str],
    key_prefix: str = ""
):
    """
    Create expandable detail rows.

    Args:
        df: DataFrame
        id_column: ID column for labeling
        display_columns: Columns to show in main view
        detail_columns: Columns to show in expanded view
        key_prefix: Key prefix
    """
    for idx, row in df.iterrows():
        with st.expander(f"{row[id_column]}", expanded=False):
            # Main info
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Main Info**")
                for col in display_columns[:len(display_columns)//2]:
                    if col in row.index:
                        st.markdown(f"- **{col}**: {row[col]}")

            with col2:
                st.markdown("**Additional Info**")
                for col in display_columns[len(display_columns)//2:]:
                    if col in row.index:
                        st.markdown(f"- **{col}**: {row[col]}")

            # Details
            if detail_columns:
                st.markdown("---")
                st.markdown("**Details**")
                detail_df = pd.DataFrame([row[detail_columns]])
                st.dataframe(detail_df, hide_index=True)


def download_button(
    df: pd.DataFrame,
    filename: str = "data.csv",
    label: str = "Download CSV"
):
    """
    Create a download button for the DataFrame.

    Args:
        df: DataFrame to download
        filename: Output filename
        label: Button label
    """
    csv = df.to_csv(index=False)
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )
