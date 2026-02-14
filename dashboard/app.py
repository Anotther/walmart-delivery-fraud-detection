"""
Walmart Fraud Detection Dashboard - Entry Point
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dashboard.components import load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache
from src.config.risk_thresholds import RiskThresholds

st.set_page_config(
    page_title="Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Global CSS
load_css()
render_sidebar()

@st.cache_data(ttl=900)
def get_home_context():
    """
    Retrieve lightweight context for the onboarding home page.
    Data is optional; page should still render when cache/database is unavailable.
    """
    context = {
        "data_period": None,
        "alert_threshold": RiskThresholds.ALERT,
    }

    try:
        cache = get_default_cache()
        metrics = cache.get_overview_metrics()
        context["data_period"] = (
            f"{metrics['date_range_start']} to {metrics['date_range_end']}"
        )
    except Exception:
        pass

    return context


context = get_home_context()

st.markdown(
    """
    <div class="dashboard-header-row">
        <div>
            <h1 style="margin:0; font-size: 2.25rem;">Walmart Fraud Control</h1>
            <p class="text-muted">This page prepares users for the analytics modules available in the sidebar.</p>
        </div>
        <div class="scope-badge-container">
            <span class="badge badge-success">Getting Started</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
This dashboard is organized as an investigation journey.
Each module provides one risk lens so teams can move from executive context to operational action.
Use the sidebar to follow the recommended sequence or jump directly to the module you need.
"""
)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### What You Will Find")
    st.markdown(
        """
- **Overview**: executive summary, risk concentration, and temporal behavior.
- **Monitor**: near-real-time signals and operational risk feed.
- **Drivers / Customers**: entity-level behavior and suspicious profiles.
- **Geographic / Product Analysis**: regional and product-level concentration.
- **Patterns / Methodology / Model Performance**: analytical rationale and model monitoring.
"""
    )

with col_right:
    st.markdown("#### Recommended Navigation")
    st.markdown(
        """
1. Start with **Overview** to establish baseline context.
2. Go to **Monitor** to view current operational pressure.
3. Investigate **Drivers** and **Customers** to identify root entities.
4. Use **Geographic** and **Product Analysis** to prioritize interventions.
5. Validate assumptions in **Patterns** and **Model Performance**.
"""
    )

st.markdown("---")
st.markdown("#### Data Availability")

if context["data_period"]:
    st.markdown(
        f"""
<div class="insight-card compact data-context-card" style="min-height: auto;">
    <div class="insight-header">
        <span class="insight-title">Data Context</span>
    </div>
    <div class="insight-body">
        Dataset coverage: <strong>{context["data_period"]}</strong><br>
        Operational alert threshold: <strong>{context["alert_threshold"]:.0f}</strong>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    st.info(
        "Data context is temporarily unavailable. Modules are still accessible from the sidebar."
    )
