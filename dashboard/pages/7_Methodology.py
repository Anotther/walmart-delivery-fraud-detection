"""
Methodology Page - Data quality, structure, and analysis details.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import load_css, kpi_card, COLORS, render_sidebar
from src.dashboard.data_cache import get_default_cache

st.set_page_config(page_title="Methodology - Walmart Fraud Detection", page_icon="📚", layout="wide")
load_css()
render_sidebar()

st.title("Data Methodology & Quality")
st.markdown("Transparency report on data structure, quality checks, and feature engineering logic.")

@st.cache_data(ttl=900)
def get_meta_data():
    cache = get_default_cache()
    return cache.get_methodology_metadata()

try:
    with st.spinner("Analyzing data lineage..."):
        meta = get_meta_data()
        dq = meta['data_quality']

    # 1. Scope & Scale
    # ----------------
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    
    with row1_col1:
        kpi_card("Deliveries Analyzed", f"{meta['total_orders']:,}", color=COLORS['walmart_blue'])
    
    with row1_col2:
        kpi_card("Analysis Period", f"{meta['date_start']} to {meta['date_end']}", color=COLORS['walmart_blue']) # Truncated in card, maybe better to split?
        
    with row1_col3:
        # Simple quality score: 100 - (bad_rows / total_rows * 100)
        total_issues = dq['orders_missing_driver'] + dq['orders_negative_amount']
        score = 100 - (total_issues / meta['total_orders'] * 100)
        kpi_card("Data Quality Score", f"{score:.1f}%", color=COLORS['success'])

    with row1_col4:
        kpi_card("Features Engineered", len(meta['features']), color=COLORS['walmart_yellow'])

    st.divider()

    # 2. Data Structure & Schema
    # --------------------------
    st.subheader("Data Structure")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Orders", "Drivers", "Customers", "Products"])
    
    with tab1:
        st.markdown("""
        **Source**: Operational Database (ETL Extracted)
        - **Primary Key**: `order_id`
        - **Key Links**: `driver_id`, `customer_id`
        - **Grain**: One row per delivery attempt
        """)
        st.info("Validation: Checked for negative order amounts and future dates.")
        
    with tab2:
        st.markdown("""
        **Source**: HR & Partner Systems
        - **Primary Key**: `driver_id`
        - **Key Attributes**: Age, Total Trips, Tenure
        """)
        st.info(f"Quality Check: {dq['drivers_missing_age']} drivers with missing age (Imputed with median).")

    with tab3:
        st.markdown("""
        **Source**: User Accounts
        - **Primary Key**: `customer_id`
        - **Segments**: `spending_segment` (Derived from total_spent)
        """)

    with tab4:
        st.markdown("""
        **Source**: Inventory Management
        - **Primary Key**: `product_id`
        - **Hierarchy**: Category -> Product Name
        """)

    st.divider()

    # 3. Data Treatments
    # ------------------
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.subheader("Cleaning & Treatments")
        st.markdown("""
        The following processing steps are applied to the raw data:
        1.  **Currency Normalization**: Removal of '$' and ',' symbols; conversion to float.
        2.  **Date Parsing**: Standardization of datetime formats to ISO-8601.
        3.  **Null Imputation**: 
            - Missing `items_missing` -> 0
            - Missing `items_delivered` -> 0
        4.  **Outlier Handling**: Negative values flagged and excluded from calc.
        """)
        
    with col_t2:
        st.subheader("Feature Logic")
        
        st.markdown("#### Driver Risk Score")
        st.code("""
Risk Score = (Missing Rate * 0.40) + 
             (Frequency Rate * 0.35) + 
             (Volume Score * 0.25)
        """, language="python")
        
        st.markdown("#### Missing Rate")
        st.latex(r'''
        \text{Missing Rate} = \frac{\text{Total Items Reported Missing}}{\text{Total Items Delivered} + \text{Total Items Missing}} \times 100
        ''')

    # 4. Raw Quality Metrics
    # ----------------------
    with st.expander("View Raw Quality Metrics"):
        st.json(dq)

except Exception as e:
    st.error(f"Error loading methodology data: {e}")
