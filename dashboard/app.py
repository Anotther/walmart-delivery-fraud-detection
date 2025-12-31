"""
Walmart Fraud Detection Dashboard - Main Application
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0071ce;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""

    # Sidebar
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg",
        width=150
    )
    st.sidebar.title("Navigation")
    st.sidebar.markdown("---")

    # Navigation info
    st.sidebar.markdown("""
    ### Pages
    - **Overview**: Key metrics and summary
    - **Orders**: Order analysis
    - **Drivers**: Driver performance
    - **Customers**: Customer analysis
    - **Fraud Detection**: Risk scoring
    - **Geographic**: Regional analysis
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This dashboard provides insights into delivery fraud patterns "
        "for Walmart e-commerce in Central Florida."
    )

    # Main content
    st.markdown('<p class="main-header">Walmart Fraud Detection System</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">E-commerce Delivery Fraud Analysis - Central Florida 2023</p>',
        unsafe_allow_html=True
    )

    # Load data
    try:
        from src.etl.extractors import extract_all
        from src.etl.transformers import transform_all
        from src.features.aggregations import get_overall_statistics

        with st.spinner("Loading data..."):
            raw_data = extract_all()
            data = transform_all(raw_data)

            orders = data["orders"]
            drivers = data["drivers"]
            customers = data["customers"]

            stats = get_overall_statistics(orders, drivers, customers)

        # Key metrics
        st.markdown("### Key Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Orders",
                value=f"{stats['total_orders']:,}"
            )

        with col2:
            st.metric(
                label="Total Revenue",
                value=f"${stats['total_revenue']:,.0f}"
            )

        with col3:
            st.metric(
                label="Missing Rate",
                value=f"{stats['overall_missing_rate']:.2f}%",
                delta="-0.5%" if stats['overall_missing_rate'] < 10 else "+0.5%",
                delta_color="inverse"
            )

        with col4:
            st.metric(
                label="Orders with Issues",
                value=f"{stats['orders_with_missing']:,}",
                delta=f"{stats['pct_orders_with_missing']:.1f}%"
            )

        st.markdown("---")

        # Second row of metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Drivers",
                value=f"{stats['active_drivers']:,}"
            )

        with col2:
            st.metric(
                label="Active Customers",
                value=f"{stats['active_customers']:,}"
            )

        with col3:
            st.metric(
                label="Regions Covered",
                value=f"{stats['total_regions']}"
            )

        with col4:
            st.metric(
                label="Items Missing",
                value=f"{stats['total_items_missing']:,}"
            )

        st.markdown("---")

        # Quick insights
        st.markdown("### Quick Insights")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top Issues")
            st.markdown(f"""
            - **{stats['pct_orders_with_missing']:.1f}%** of orders have missing items
            - **{stats['total_items_missing']:,}** total items reported as missing
            - Average order value: **${stats['avg_order_value']:.2f}**
            """)

        with col2:
            st.markdown("#### Data Coverage")
            st.markdown(f"""
            - Date range: **{stats['date_range_start']}** to **{stats['date_range_end']}**
            - Total drivers in system: **{stats['total_drivers']}**
            - Total customers in system: **{stats['total_customers']}**
            """)

        st.markdown("---")

        # Navigation cards
        st.markdown("### Explore Data")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            #### 📦 Orders Analysis
            Analyze order patterns, missing items distribution,
            and identify high-risk orders.

            👉 Go to **Orders** page
            """)

        with col2:
            st.markdown("""
            #### 🚗 Driver Performance
            Review driver statistics, identify suspicious drivers,
            and analyze delivery patterns.

            👉 Go to **Drivers** page
            """)

        with col3:
            st.markdown("""
            #### 👥 Customer Behavior
            Understand customer patterns, identify repeat offenders,
            and analyze spending behavior.

            👉 Go to **Customers** page
            """)

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            #### 🎯 Fraud Detection
            View risk scores, anomaly detection results,
            and prioritized investigation list.

            👉 Go to **Fraud Detection** page
            """)

        with col2:
            st.markdown("""
            #### 🗺️ Geographic Analysis
            Explore regional patterns, identify hotspots,
            and compare regional performance.

            👉 Go to **Geographic** page
            """)

        with col3:
            st.markdown("""
            #### 📊 Reports
            Generate comprehensive reports and
            export data for further analysis.

            👉 Coming soon
            """)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure the data files are in the 'data/' directory.")

        st.markdown("### Troubleshooting")
        st.code("""
        # Required data files:
        data/orders.csv
        data/customers_data.csv
        data/drivers_data.csv
        data/products_data.csv
        data/missing_items_data.csv
        """)


if __name__ == "__main__":
    main()
