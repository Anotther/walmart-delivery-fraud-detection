"""
Walmart Fraud Detection Dashboard - Entry Point
"""
import streamlit as st

# Minimal page config - must be first Streamlit command
st.set_page_config(
    page_title="Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🛒 Walmart Fraud Detection System")

st.markdown("""
## Welcome to the Fraud Detection Dashboard

This dashboard provides comprehensive fraud analysis for Walmart e-commerce deliveries.

### Available Pages

Navigate through the sidebar to access different analysis modules:

1. **Overview** - Executive summary and KPIs
2. **Monitor** - Real-time operational dashboard
3. **Drivers** - Driver risk analysis
4. **Customers** - Customer behavior patterns
5. **Geographic** - Regional hotspot analysis
6. **Product Analysis** - Product-level fraud patterns
7. **Methodology** - Model documentation
8. **Patterns** - Statistical fraud patterns
9. **Model Performance** - ML model monitoring

### Getting Started

Use the sidebar navigation (☰ menu) to explore different analysis modules.

---

**Note**: This is the home page. Select a page from the sidebar to view detailed analytics.
""")

# Status indicator
st.success("✅ Dashboard is ready. Select a page from the sidebar to begin.")
