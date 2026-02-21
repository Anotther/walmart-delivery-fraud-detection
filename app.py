"""
Walmart Fraud Detection Dashboard - Entry Point
"""
import logging
import streamlit as st
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.dashboard.components import load_css, render_sidebar
    from src.dashboard.data_cache import get_default_cache
    from src.config.risk_thresholds import RiskThresholds
    imports_successful = True
except Exception as e:
    logger.error(f"Failed to import modules: {e}", exc_info=True)
    imports_successful = False
    class RiskThresholds:
        ALERT = 75

st.set_page_config(
    page_title="Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Global CSS
if imports_successful:
    try:
        load_css()
        render_sidebar()
    except Exception as e:
        logger.warning(f"Failed to load CSS or sidebar: {e}")

@st.cache_data(ttl=900)
def get_home_context():
    """Retrieve lightweight context for the home page."""
    context = {
        "data_period": None,
        "alert_threshold": RiskThresholds.ALERT,
    }

    if not imports_successful:
        return context

    try:
        cache = get_default_cache()
        metrics = cache.get_overview_metrics()
        context["data_period"] = (
            f"{metrics['date_range_start']} to {metrics['date_range_end']}"
        )
    except Exception as exc:
        logger.warning(f"Unable to load dashboard context: {exc}", exc_info=True)

    return context

try:
    context = get_home_context()
except Exception as e:
    logger.error(f"Failed to get home context: {e}", exc_info=True)
    context = {"data_period": None, "alert_threshold": 75}

st.markdown("""
<div class="dashboard-header-row">
    <div>
        <h1 style="margin:0; font-size: 2.25rem;">Walmart Fraud Control</h1>
        <p class="text-muted">Fraud Detection & Analytics Dashboard</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This dashboard provides comprehensive fraud analysis for Walmart e-commerce deliveries in Central Florida.

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

### Recommended Navigation

1. Start with **Overview** to establish baseline context
2. Go to **Monitor** to view current operational pressure
3. Investigate **Drivers** and **Customers** to identify root entities
4. Use **Geographic** and **Product Analysis** to prioritize interventions
5. Validate assumptions in **Patterns** and **Model Performance**
""")

st.markdown("---")

if context["data_period"]:
    st.markdown(f"""
**Data Coverage**: {context['data_period']}

**Alert Threshold**: {context['alert_threshold']:.0f}
""")
else:
    st.info("Data context is being loaded. Check individual pages for detailed analytics.")

st.success("✅ Dashboard is ready. Select a page from the sidebar to begin analysis.")
