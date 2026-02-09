"""
Products Page - Analysis of missing products and losses.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import load_css, kpi_card, plot_bar_chart, COLORS, render_sidebar

from src.dashboard.data_cache import get_default_cache

@st.cache_data(ttl=900)
def get_product_data():
    cache = get_default_cache()
    return cache.get_product_summary()

def main():
    render_sidebar()

    st.title("Product Analysis")
    st.markdown("Loss analysis by SKU and product category.")

    with st.spinner("Loading product data..."):
        df = get_product_data()

    # Derived Metrics
    total_missing_qty = df['times_reported_missing'].sum() if not df.empty else 0
    total_financial_loss = df['estimated_loss'].sum() if not df.empty else 0
    
    most_missed_name = "N/A"
    top_cat_name = "N/A"
    
    if not df.empty:
        most_missed_row = df.loc[df['times_reported_missing'].idxmax()]
        most_missed_name = f"{most_missed_row['product_name']} ({most_missed_row['times_reported_missing']} units)"
        
        # Category analysis
        cat_loss = df.groupby("category")["estimated_loss"].sum()
        if not cat_loss.empty:
            top_cat_name = cat_loss.idxmax()

    # Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Total Units Missing", f"{total_missing_qty:,}", color=COLORS['walmart_blue'])
    with col2:
        kpi_card("Total Estimated Loss", f"${total_financial_loss:,.0f}", color=COLORS['critical'])
    with col3:
        kpi_card("Highest Loss Category", top_cat_name, color=COLORS['warning'])
    with col4:
        # Just show name if too long
        display_name = most_missed_name.split('(')[0].strip()
        kpi_card("Top Missing Product", display_name, color=COLORS['walmart_yellow'])

    st.markdown("---")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.subheader("Top Products by Financial Loss")
        if not df.empty:
            st.dataframe(
                df.sort_values("estimated_loss", ascending=False).head(10)[[
                    "product_name", "category", "times_reported_missing", "price", "estimated_loss"
                ]].style.format({
                    "price": "${:.2f}",
                    "estimated_loss": "${:,.2f}"
                }),
                column_config={
                    "product_name": "Product",
                    "category": "Category",
                    "times_reported_missing": "Missing Qty",
                    "price": "Unit Price",
                    "estimated_loss": "Total Loss"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No product data available.")

    with col_side:
        st.subheader("Loss by Category")
        if not df.empty:
            df_cat = df.groupby("category")["estimated_loss"].sum().reset_index()
            plot_bar_chart(df_cat, "category", "estimated_loss", "Financial Loss by Category")
        else:
            st.info("No category data available.")

if __name__ == "__main__":
    main()
