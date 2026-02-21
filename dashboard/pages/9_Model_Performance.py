"""
Model Performance - MLOps dashboard for tracking drift, retraining, and strategy.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import load_css, kpi_card, COLORS, render_sidebar, risk_badge
from src.dashboard.data_cache import get_default_cache

st.set_page_config(page_title="Model Performance - Walmart Fraud Detection", page_icon="🤖", layout="wide")
load_css()
render_sidebar()

st.title("Model Performance & MLOps")
st.markdown("Monitoring Isolation Forest efficacy, data drift, and algorithmic stability.")

@st.cache_data(ttl=600)  # 10-minute TTL for model performance data
def get_mlops_data():
    """
    Fetch model performance data using lazy loading.
    This method uses a 10-minute TTL as ML monitoring updates moderately frequently.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for model performance page
    page_data = cache.get_page_data('model_performance')

    # Extract model performance data from page data
    mlops_data = page_data['model_performance_metrics']

    return mlops_data

try:
    with st.spinner("Calculating MLOps metrics (Drift, Stability)..."):
        mlops = get_mlops_data()
        
    model_info = mlops['model_info']
    perf = mlops['performance']
    
    # 1. Strategy & Architecture
    # --------------------------
    st.header("1. Strategy & Architecture")
    col_str1, col_str2 = st.columns([1, 2])
    
    with col_str1:
        st.markdown(f"**Algorithm**: `{model_info['algorithm']}`")
        st.markdown("""
        **Why Isolation Forest?**
        - **Label Deficiency**: We lack historically confirmed fraud labels.
        - **Anomaly Focus**: Fraud mimics rare outliers (high volume, unusual hours).
        - **Scalability**: Efficient for high-volume order streams.
        """)
        
    with col_str2:
        kpi_card("Current Anomaly Rate", f"{perf['current_anomaly_rate']:.2f}%", 
                 delta=f"{perf['rate_change_pct']:.1f}% vs Ref",
                 color=COLORS['walmart_blue'])
        
    st.divider()

    # 2. MLOps Monitoring
    # -------------------
    st.header("2. MLOps Monitoring")
    
    tab_drift, tab_imp = st.tabs(["Data Drift (KS Test)", "Feature Importance"])
    
    with tab_drift:
        st.subheader("Reference vs Current Period Drift")
        drift_data = mlops.get('drift_analysis', [])
        
        if drift_data:
            drift_df = pd.DataFrame(drift_data)
            
            # Highlight drifting features
            drift_df['Status'] = drift_df['is_drifting'].apply(lambda x: 'DRIFT DETECTED' if x else 'Stable')
            
            # Simple table
            st.dataframe(
                drift_df[['feature', 'ks_stat', 'p_value', 'Status', 'curr_mean']].style.applymap(
                    lambda x: 'color: red; font-weight: bold' if x == 'DRIFT DETECTED' else 'color: green', 
                    subset=['Status']
                ),
                use_container_width=True
            )
            
            if drift_df['is_drifting'].any():
                st.warning("⚠️ Significant drift detected in key features. Model retraining recommended.")
            else:
                st.success("✅ Feature distributions are stable (p-value > 0.05).")
        else:
            st.info("No drift data available.")
            
    with tab_imp:
        st.subheader("Proxy Feature Importance")
        st.markdown("Correlation of features with observed `items_missing` events.")
        
        imp_data = mlops.get('feature_importance', {})
        if imp_data:
            imp_df = pd.DataFrame(list(imp_data.items()), columns=['Feature', 'Correlation'])
            fig_bar = px.bar(
                imp_df, 
                x='Correlation', 
                y='Feature', 
                orientation='h',
                title="Top Features correlated with Missing Items",
                color='Correlation',
                color_continuous_scale='Bluered'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # 3. Retraining Status
    # --------------------
    st.header("3. Retraining Status")
    
    col_re1, col_re2 = st.columns(2)
    
    with col_re1:
        st.subheader("Champion vs Challenger")
        st.info("Simulated A/B Test Results")
        
        ab_data = pd.DataFrame({
            "Model": ["Champion (Current)", "Challenger (Retrained)"],
            "Anomaly Rate": [perf['current_anomaly_rate'], perf['current_anomaly_rate'] * 0.95], # Mock challenger
            "Status": ["Active", "Candidate"]
        })
        st.table(ab_data)
        
    with col_re2:
        st.subheader("System Health")
        if perf['status'] == 'Stable':
             st.success("Create Risk Report: **Healthy**")
             st.markdown("- **Drift**: Low\n- **Latency**: <50ms\n- **Last Retrain**: 15 days ago")
        else:
             st.error("Create Risk Report: **Action Required**")
             st.markdown("- **Drift**: High\n- **Performance**: Degrading\n- **Action**: Approve Retraining")


except Exception as e:
    st.error(f"Error loading model metrics: {e}")
