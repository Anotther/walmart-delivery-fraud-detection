"""
Patterns Page - Advanced fraud pattern detection and algorithms.
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

st.set_page_config(page_title="Patterns - Walmart Fraud Detection", page_icon="🧬", layout="wide")
load_css()
render_sidebar()

st.title("Advanced Patterns & Algorithms")
st.markdown("Deep dive into temporal anomalies, network effects, and algorithmic detection.")

@st.cache_data(ttl=900)
def get_patterns_data():
    cache = get_default_cache()
    # Fetch data parallelly in real scenario, sequential here
    patterns = cache.get_patterns_analysis()
    temporal = cache.get_advanced_temporal()
    
    # We also need feature data for correlation
    # We can get this from driver/customer summaries
    drivers = cache.get_driver_summary()
    return patterns, temporal, drivers

try:
    with st.spinner("Running pattern recognition algorithms..."):
        patterns, temporal, drivers_df = get_patterns_data()

    # 1. Temporal Patterns
    # --------------------
    st.header("1. Temporal Patterns")
    
    # Metrics
    temp_anomalies = temporal['anomalies']
    trend = temporal['trend']
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        direction_icon = "📈" if trend['direction'] == 'increasing' else "📉"
        kpi_card("Fraud Trend", f"{trend['direction'].title()} {direction_icon}", color=COLORS['walmart_blue'])
    with col_t2:
        kpi_card("Trend Change", f"{trend['change_pct']:.1f}%", color=COLORS['warning'] if trend['change_pct'] > 0 else COLORS['success'])
    with col_t3:
        kpi_card("Temporal Anomalies", f"{temp_anomalies['total']}", color=COLORS['critical'])
    with col_t4:
        kpi_card("Peak Risk Period", f"{temporal['patterns']['worst_day']}s", color=COLORS['walmart_yellow'])

    # Heatmap & Anomalies
    col_tm, col_ts = st.columns([2, 1])
    
    with col_tm:
        st.subheader("Risk Heatmap: Hour vs Day")
        # Need to reconstruct hourly data or use the 'hourly' key if accessible
        # Since 'temporal' is summary, let's look at cache.get_temporal_trends() logic... 
        # Actually the cache method 'get_advanced_temporal' calls 'get_temporal_summary'.
        # 'get_temporal_trends' gives raw frames. 
        # We might need to fetch trends for the heatmap.
        # Let's call cache directly for trends here to be safe
        trends = get_default_cache().get_temporal_trends()
        daily = trends['daily']
        hourly = trends['hourly'] # aggregated over all days
        
        # NOTE: To do Day vs Hour heatmap we need the raw aggregation. 
        # For now, let's visualize Day of Week risk.
        fig = px.bar(
            daily, 
            x="day_of_week", 
            y="missing_rate", 
            color="missing_rate",
            title="Missing Rate by Day of Week",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_ts:
        st.subheader("Detected Anomalies")
        if temp_anomalies['total'] > 0:
            for category, items in temp_anomalies['details'].items():
                if items:
                    st.markdown(f"**{category.title()}**")
                    for item in items:
                        if 'period' in item: p = item['period']
                        elif 'day' in item: p = item['day']
                        elif 'hour' in item: p = f"{item['hour']}:00"
                        else: p = 'Unknown'
                        
                        st.error(f"{p}: Rate {item['missing_rate']:.1f}% (Threshold: {item['threshold']:.1f}%)")
        else:
            st.success("No significant temporal anomalies detected.")

    st.divider()

    # 2. Network & Correlations
    # -------------------------
    st.header("2. Network & Correlations")
    
    tab_net, tab_corr = st.tabs(["Collusion Detection", "Feature Correlations"])
    
    with tab_net:
        collusion = patterns.get('collusion_patterns', [])
        st.markdown(f"**Potential Collusion Pairs Detected**: {len(collusion)}")
        
        if collusion:
            collusion_data = []
            for p in collusion:
                collusion_data.append({
                    "Driver": p.details['driver_id'],
                    "Customer": p.details['customer_id'],
                    "Interactions": p.details['interactions'],
                    "Missing Items": p.details['items_missing'],
                    "Missing Rate": f"{p.details['missing_rate']:.1f}%",
                    "Score": p.score
                })
            st.dataframe(pd.DataFrame(collusion_data).sort_values("Score", ascending=False), use_container_width=True)
        else:
            st.info("No collusion patterns detected matching thresholds.")
            
    with tab_corr:
        st.subheader("Driver Feature Correlation")
        # Select numeric columns for correlation
        if not drivers_df.empty:
            corr_cols = ['total_orders', 'total_items_delivered', 'total_items_missing', 
                         'missing_rate', 'avg_order_value', 'risk_score']
            # Filter only existing columns
            corr_cols = [c for c in corr_cols if c in drivers_df.columns]
            
            corr = drivers_df[corr_cols].corr()
            fig_corr = px.imshow(
                corr, 
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix: Driver Risk Factors"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Insufficient data for correlation analysis.")

    st.divider()

    # 3. Algorithms Summary
    # ---------------------
    st.header("3. Algorithmic Detectors")
    
    detectors = [
        {"name": "Driver Pattern Anomalies", "count": len(patterns.get('driver_patterns', [])), "desc": "Deviation from peer benchmarks (Mean + 2SD)"},
        {"name": "Customer Claim Frequency", "count": len(patterns.get('customer_patterns', [])), "desc": "Abnormal claim velocity vs spend"},
        {"name": "Network Collusion", "count": len(patterns.get('collusion_patterns', [])), "desc": "Driver-Customer recurrent loss pairings"},
        {"name": "Regional Hotspots", "count": len(patterns.get('regional_patterns', [])), "desc": "Geospatial high-risk zones"},
    ]
    
    col_alg1, col_alg2 = st.columns([1, 1])
    
    with col_alg1:
        st.markdown("### Active Detectors Status")
        for d in detectors:
            status_color = "red" if d['count'] > 0 else "green"
            st.markdown(f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid {status_color}">
                <strong>{d['name']}</strong><br>
                <span style="font-size: 0.9em; color: #666;">{d['desc']}</span>
                <div style="float: right; font-weight: bold;">{d['count']} Findings</div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_alg2:
         st.markdown("### Latest Findings Log")
         # Flatten all patterns
         all_findings = []
         for p_type, items in patterns.items():
            for item in items:
                all_findings.append({
                    "Algorithm": p_type.replace('_patterns', '').title(),
                    "Entity": item.entity_id,
                    "Score": item.score,
                    "Indicator": item.indicator_name
                })
         
         if all_findings:
             df_log = pd.DataFrame(all_findings).sort_values("Score", ascending=False).head(10)
             st.dataframe(df_log, use_container_width=True, hide_index=True)
         else:
             st.success("Clean log. No active findings.")

except Exception as e:
    st.error(f"Error loading patterns: {e}")
