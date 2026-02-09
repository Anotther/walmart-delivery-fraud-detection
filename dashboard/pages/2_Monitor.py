"""
Monitor & Insights - Walmart Fraud Detection
A comprehensive, data-driven monitoring dashboard connecting hypotheses to results.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from html import escape

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Explicit imports to avoid any potential namespace issues
import importlib
import src.dashboard.components
importlib.reload(src.dashboard.components)

from src.dashboard.components import load_css
from src.dashboard.components import kpi_card
from src.dashboard.components import insight_card
from src.dashboard.components import plot_bar_chart
from src.dashboard.components import plot_line_chart
from src.dashboard.components import plot_dual_axis_trend
from src.dashboard.components import plot_correlation_heatmap
from src.dashboard.components import plot_hypothesis_card
from src.dashboard.components import plot_drift_card
from src.dashboard.components import risk_badge
from src.dashboard.components import render_sidebar
from src.dashboard.components import COLORS

from src.dashboard.data_cache import get_default_cache

st.set_page_config(page_title="Monitor - Walmart Fraud Detection", page_icon="📡", layout="wide")
load_css()

@st.cache_data(ttl=300)
def get_dashboard_data():
    cache = get_default_cache()
    data = cache.get_monitoring_dashboard_data()
    hypotheses = cache.get_hypothesis_results()
    patterns = cache.get_emerging_patterns()
    performance = cache.get_model_performance_metrics()
    return data, hypotheses, patterns, performance


def render_feature_drift_table(drift_df: pd.DataFrame) -> None:
    """Render a modern drift table card with hover tooltip inside the header."""
    if drift_df.empty:
        st.info("No drift features available.")
        return

    drift_view = drift_df.copy()
    drift_view["status_label"] = drift_view["is_drifting"].map(lambda x: "Drifting" if x else "Stable")
    drift_view["status_icon"] = drift_view["is_drifting"].map(lambda x: "🔴" if x else "🟢")

    rows_html = []
    for _, row in drift_view.iterrows():
        is_drifting = bool(row.get("is_drifting", False))
        status_class = "drift-chip-alert" if is_drifting else "drift-chip-ok"
        rows_html.append(
            (
                "<tr>"
                f"<td>{escape(str(row.get('feature', '-')))}</td>"
                f"<td><span class='drift-chip {status_class}'>{row.get('status_icon', '🟢')} {escape(str(row.get('status_label', '-')))}</span></td>"
                f"<td>{float(row.get('p_value', 0.0)):.3f}</td>"
                f"<td>{float(row.get('ks_stat', 0.0)):.3f}</td>"
                f"<td>{float(row.get('ref_mean', 0.0)):.2f}</td>"
                f"<td>{float(row.get('curr_mean', 0.0)):.2f}</td>"
                "</tr>"
            )
        )

    table_html = f"""
    <style>
      .drift-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
        overflow: hidden;
      }}
      .drift-card-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        padding: 0.7rem 0.8rem;
        border-bottom: 1px solid var(--border-light);
        background: #fafbfc;
      }}
      .drift-card-title {{
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--walmart-blue-dark);
      }}
      .drift-card-hint {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1rem;
        height: 1rem;
        border-radius: 999px;
        border: 1px solid #cbd5e1;
        color: #334155;
        font-size: 0.65rem;
        background: #ffffff;
        cursor: help;
        flex-shrink: 0;
      }}
      .drift-table-wrap {{
        width: 100%;
        overflow-x: auto;
      }}
      .drift-table {{
        width: 100%;
        border-collapse: collapse;
      }}
      .drift-table thead th {{
        text-align: left;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: .03em;
        color: #64748b;
        font-weight: 700;
        padding: 0.55rem 0.6rem;
        border-bottom: 1px solid var(--border-light);
      }}
      .drift-table tbody td {{
        font-size: 0.84rem;
        color: #0f172a;
        padding: 0.52rem 0.6rem;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: middle;
      }}
      .drift-table tbody tr:last-child td {{
        border-bottom: none;
      }}
      .drift-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.24rem;
        font-size: 0.74rem;
        font-weight: 700;
        border-radius: 999px;
        padding: 0.12rem 0.5rem;
        border: 1px solid transparent;
      }}
      .drift-chip-ok {{
        color: #166534;
        background: #dcfce7;
        border-color: #bbf7d0;
      }}
      .drift-chip-alert {{
        color: #991b1b;
        background: #fee2e2;
        border-color: #fecaca;
      }}
    </style>
    <div class="drift-card">
      <div class="drift-card-head">
        <span class="drift-card-title">Feature Drift Analysis (KS-Test)</span>
        <span
          class="drift-card-hint"
          title="KS-test compara a distribuição atual com a referência. p-value menor que 0.05 indica drift estatístico."
        >ⓘ</span>
      </div>
      <div class="drift-table-wrap">
        <table class="drift-table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Status</th>
              <th>p-value</th>
              <th>KS Stat</th>
              <th>Ref Mean</th>
              <th>Current Mean</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def main():
    render_sidebar()
    data, hypotheses, patterns, performance = get_dashboard_data()
    cache = get_default_cache()  # Get cache instance for additional methods
    
    # -------------------------------------------------------------------------
    # 1. Header & Context (Updated Style)
    # -------------------------------------------------------------------------
    st.markdown("### Operational Intelligence")
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
            <h1 style="margin:0; font-size: 2.5rem;">Fraud Monitor Intelligence</h1>
            <p class="text-muted">Real-time monitoring and hypothesis validation engine for Central Florida.</p>
        </div>
        <div style="text-align: right;">
             <span class="badge badge-success">System Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Executive Dashboard (Simulated "Top-Level" View)
    # -------------------------------------------------------------------------
    st.markdown("#### 📊 Executive Summary")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Fraud Exposure", f"${data['kpis']['fraud_exposure']:,.0f}", delta="-12%", delta_color="inverse", tooltip="Estimated value of missing items")
    with k2:
        kpi_card("Missing Rate", f"{data['kpis']['missing_rate']:.2f}%", delta="-0.5%", delta_color="inverse", tooltip="Percentage of items reported missing")
    with k3:
        kpi_card("High Risk Entities", str(int(data['kpis']['high_risk_entities'])), delta="+3", delta_color="inverse", tooltip="Drivers & Customers in Critical status")
    with k4:
        kpi_card("Model Accuracy", f"{data['kpis']['model_performance']}%", delta="+1.2%", delta_color="normal", tooltip="Current model precision")
    with k5:
        # Green KPI for positive impact
        kpi_card("Est. Monthly Savings", f"${data['kpis']['monthly_savings']:,.0f}", delta="ROI 4.2x", color=COLORS['success'], tooltip="Projected savings from fraud prevention")

    # -------------------------------------------------------------------------
    # 2b. Business Context & Strategy (Custom Visual Component)
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div style="background-color: var(--bg-card); padding: 1.5rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border: 1px solid var(--border-light); margin-bottom: 2rem; margin-top: 2rem;">
        <div style="display: flex; flex-wrap: wrap; gap: 2rem; align-items: center;">
            <div style="flex: 3; min-width: 300px;">
                <h3 style="margin-top: 0; font-size: 1.1rem; color: var(--walmart-blue-dark); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                    ℹ️ Business Context & Strategy
                </h3>
                <p style="color: var(--text-secondary); margin-bottom: 1rem; line-height: 1.6;">
                    <strong>The Challenge:</strong> Walmart delivery operations face systematic inventory loss ("missing items") that impacts profitability and customer trust. Traditional rule-based controls were insufficient against sophisticated fraud patterns.
                </p>
                <div style="background-color: var(--bg-primary); padding: 1rem; border-radius: var(--radius-sm); border-left: 3px solid var(--walmart-yellow);">
                    <strong style="color: var(--walmart-blue-dark); display: block; margin-bottom: 0.25rem;">The AI Solution:</strong>
                    <span style="color: var(--text-primary); font-size: 0.9rem;">
                        Real-time monitoring engine using Isolation Forests to detect <strong style="color: var(--walmart-blue);">Organized Collusion</strong>, <strong style="color: var(--walmart-blue);">Repeat Offenders</strong>, and <strong style="color: var(--walmart-blue);">Regional Gaps</strong>.
                    </span>
                </div>
            </div>
            <div style="flex: 1; min-width: 220px; display: flex; justify-content: flex-end;">
                 <div style="text-align: center; padding: 1.25rem; background: linear-gradient(to bottom right, #f0f9ff, #e0f2fe); border-radius: var(--radius-md); border: 1px solid #bae6fd; width: 100%;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.5rem;">Strategic Goal</div>
                    <div style="font-size: 2rem; font-weight: 800; color: var(--walmart-blue); line-height: 1;">&lt; 10%</div>
                    <div style="font-weight: 600; color: var(--walmart-blue-dark); margin-top: 0.25rem; font-size: 0.9rem;">Missing Rate</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">by Q3 2024</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. Analytical Approach & Hypotheses (The "Why")
    # -------------------------------------------------------------------------
    st.markdown("#### 🧬 Analytical Approach & Hypotheses")
    st.caption("Validating strategic assumptions with statistical rigor to drive detection logic.")

    active_hypotheses = hypotheses  # From cache
    
    # Process in batches of 2 for grid alignment
    for i in range(0, len(active_hypotheses), 2):
        row_hypotheses = active_hypotheses[i:i+2]
        cols = st.columns(2)
        
        for j, h in enumerate(row_hypotheses):
            with cols[j]:
                plot_hypothesis_card(
                    id=h['id'],
                    statement=h['statement'],
                    status=h['status'],
                    result_text=h['result_text'],
                    methodology=h['methodology'],
                    p_value=h.get('p_value'),
                    metric_name=h.get('metric_name'),
                    metric_value=h.get('metric_value')
                )
                
                # Show visual evidence if available
                if h.get('visual_data') and h['status'] == 'Validated':
                    with st.expander("📊 View Evidence", expanded=False):
                        if h['id'] == 'H1': # Driver Experience
                            df_ev = pd.DataFrame(h['visual_data'])
                            fig = px.scatter(
                                df_ev, x='orders_completed', y='missing_rate', 
                                title="Driver Experience vs Missing Rate",
                                opacity=0.6,
                                color_discrete_sequence=[COLORS['walmart_blue']],
                                labels={'orders_completed': 'Total Orders', 'missing_rate': 'Missing Rate (%)'}
                            )
                            fig.update_layout(height=250, margin=dict(t=30, l=0, r=0, b=0))
                            st.plotly_chart(fig, use_container_width=True)
                            
                        elif h['id'] == 'H2': # Region
                            df_ev = pd.DataFrame(h['visual_data'])
                            fig = px.bar(
                                df_ev.sort_values('missing_rate', ascending=False), 
                                x='region', y='missing_rate',
                                title="Regional Variance",
                                color='missing_rate',
                                color_continuous_scale='Reds',
                                labels={'missing_rate': 'Missing Rate (%)'}
                            )
                            fig.update_layout(height=250, margin=dict(t=30, l=0, r=0, b=0))
                            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    # -------------------------------------------------------------------------
    # 4. Operational Watchtower (Real-Time Intelligence)
    # -------------------------------------------------------------------------
    st.markdown("#### 🔭 Operational Watchtower")
    st.caption("Live system monitoring with statistical anomaly detection and threat assessment.")
    
    # Get hourly monitoring data
    hourly_monitor = cache.get_hourly_monitoring_data()
    
    # Level 1: System Status Board
    st.markdown("##### System Status")
    stat1, stat2, stat3, stat4 = st.columns(4)
    
    with stat1:
        # Threat Level Indicator
        threat_level = hourly_monitor['threat_level']
        threat_color = hourly_monitor['threat_color']
        sigma = hourly_monitor['sigma_deviation']
        
        st.markdown(f"""
        <div style="background: {threat_color}15; border: 2px solid {threat_color}; border-radius: 8px; padding: 1rem; text-align: center;">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #6b7280; font-weight: 600; margin-bottom: 0.5rem;">Threat Level</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: {threat_color}; margin-bottom: 0.25rem;">{threat_level}</div>
            <div style="font-size: 0.8rem; color: #6b7280;">{sigma:+.2f}σ from baseline</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat2:
        st.metric(
            "Active Anomalies",
            hourly_monitor['active_anomalies'],
            delta=f"Detected in last 24h",
            delta_color="inverse"
        )
    
    with stat3:
        st.metric(
            "Orders Monitored",
            f"{hourly_monitor['total_orders_24h']:,}",
            delta=f"{hourly_monitor['clean_rate_24h']:.1f}% Clean"
        )
    
    with stat4:
        current_vs_baseline = hourly_monitor['current_rate'] - hourly_monitor['baseline_rate']
        st.metric(
            "Current Rate",
            f"{hourly_monitor['current_rate']:.2f}%",
            delta=f"{current_vs_baseline:+.2f}pp vs baseline",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Level 2: Hourly Anomaly Detection Chart
    st.markdown("##### Hourly Anomaly Detection (24-Hour Profile)")
    
    hourly_df = hourly_monitor['hourly_data']
    
    # Create dual-line chart with baseline
    fig = go.Figure()
    
    # Baseline (Expected)
    fig.add_trace(go.Scatter(
        x=hourly_df['hour'],
        y=hourly_df['baseline'],
        name='Baseline (Expected)',
        line=dict(color='#9ca3af', width=2, dash='dash'),
        mode='lines'
    ))
    
    # Upper threshold
    fig.add_trace(go.Scatter(
        x=hourly_df['hour'],
        y=hourly_df['upper_threshold'],
        name='Alert Threshold (+2σ)',
        line=dict(color='#fbbf24', width=1, dash='dot'),
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(251, 191, 36, 0.1)'
    ))
    
    # Actual data - split into normal and anomaly points
    normal_data = hourly_df[~hourly_df['is_anomaly']]
    anomaly_data = hourly_df[hourly_df['is_anomaly']]
    
    # Normal points
    fig.add_trace(go.Scatter(
        x=normal_data['hour'],
        y=normal_data['missing_rate'],
        name='Actual (Normal)',
        line=dict(color=COLORS['walmart_blue'], width=3),
        mode='lines+markers',
        marker=dict(size=6, color=COLORS['walmart_blue'])
    ))
    
    # Anomaly points
    if len(anomaly_data) > 0:
        fig.add_trace(go.Scatter(
            x=anomaly_data['hour'],
            y=anomaly_data['missing_rate'],
            name='Anomaly Detected',
            mode='markers',
            marker=dict(size=12, color=COLORS['critical'], symbol='x', line=dict(width=2, color='white'))
        ))
    
    fig.update_layout(
        title="Missing Rate by Hour (Actual vs Expected Baseline)",
        xaxis_title="Hour of Day",
        yaxis_title="Missing Rate (%)",
        hovermode="x unified",
        height=400,
        font_family="Inter",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f3f4f6')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f3f4f6')
    
    st.plotly_chart(fig, use_container_width=True, key="hourly_anomaly_chart")
    
    st.caption("📊 **Statistical Grounding:** Anomalies are defined as data points exceeding 2 standard deviations (σ) above the hourly baseline. This method accounts for natural hourly variance in delivery patterns.")
    
    st.markdown("---")
    
    # Level 3: Live Alert Feed
    col_feed, col_insight = st.columns([2, 1])
    
    with col_feed:
        with st.expander("🚨 Live Risk Feed (Recent Alerts)", expanded=True):
            alerts_df = data['alerts']
            
            if not alerts_df.empty:
                # Show top 5 most recent/critical
                top_alerts = alerts_df.head(5)
                
                for idx, alert in top_alerts.iterrows():
                    timestamp = datetime.now() - timedelta(hours=idx+1)  # Simulated timestamps
                    time_str = timestamp.strftime("%H:%M")
                    
                    severity_icon = "🔴" if alert['risk_score'] >= 80 else "🟡"
                    
                    st.markdown(f"""
                    <div style="background: #f9fafb; border-left: 3px solid {COLORS['critical'] if alert['risk_score'] >= 80 else COLORS['warning']}; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <span style="font-size: 0.75rem; color: #6b7280; font-weight: 600;">[{time_str}]</span>
                                <span style="margin-left: 0.5rem; font-weight: 600; color: #111827;">{severity_icon} {alert['entity_type'].upper()}</span>
                                <span style="margin-left: 0.25rem; color: #4b5563;">#{alert['entity_name']}</span>
                            </div>
                            <div style="background: {COLORS['critical'] if alert['risk_score'] >= 80 else COLORS['warning']}20; color: {COLORS['critical'] if alert['risk_score'] >= 80 else COLORS['warning']}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">
                                Risk: {alert['risk_score']:.0f}
                            </div>
                        </div>
                        <div style="margin-top: 0.25rem; font-size: 0.85rem; color: #6b7280;">
                            {alert['primary_metric']} | {alert['recommendation']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No critical alerts in the last 24 hours. System operating normally.")
    
    with col_insight:
        # Emerging Pattern Insight
        pattern_df = patterns
        if not pattern_df.empty and len(pattern_df) > 0:
            latest_pattern = pattern_df.iloc[0]
            pattern_name = escape(str(latest_pattern['pattern_name']))
            pattern_severity = escape(str(latest_pattern['severity']))
            pattern_description = escape(str(latest_pattern['description']))
            detection_date = escape(str(latest_pattern['detection_date']))
            pattern_content = (
                f"<strong>{pattern_name}</strong><br>"
                f"<span style=\"color: #6b7280; font-size: 0.9rem;\">Severity: {pattern_severity}</span><br><br>"
                f"{pattern_description}<br><br>"
                f"<span style=\"font-size: 0.85rem; color: #6b7280;\">Detected: {detection_date}</span>"
            )
            insight_card(
                title="🔍 Latest Pattern Detected",
                content=pattern_content,
                icon="⚠️"
            )
        else:
            st.info("💡 **Insight:** System baseline is stable. No new patterns detected in recent monitoring window.")


    # -------------------------------------------------------------------------
    # 5. Model Performance (MLOps)
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("🛠️ Model Performance & MLOps (Technical View)", expanded=True):
        perf_data = performance['performance']
        drift_data = performance['drift_analysis']
        drift_df = pd.DataFrame(drift_data)

        total_features = len(drift_df)
        drifting_features = int(drift_df['is_drifting'].sum()) if not drift_df.empty else 0
        current_anomaly_rate = float(perf_data['current_anomaly_rate'])
        reference_anomaly_rate = float(perf_data['reference_anomaly_rate'])
        clean_rate_proxy = max(0.0, 100 - current_anomaly_rate)

        today = datetime.now().date()
        quarterly_months = [2, 5, 8, 11]
        next_quarterly_date = None
        for month in quarterly_months:
            candidate = datetime(today.year, month, 15).date()
            if candidate >= today:
                next_quarterly_date = candidate
                break
        if next_quarterly_date is None:
            next_quarterly_date = datetime(today.year + 1, quarterly_months[0], 15).date()
        days_until_retraining = (next_quarterly_date - today).days

        if perf_data['status'] == "Stable" and drifting_features == 0:
            st.success("Model health is stable. No immediate retraining signal was detected.")
        elif drifting_features > 0:
            st.warning("Feature drift detected. Review drifted features and consider expedited retraining.")
        else:
            st.info("Anomaly profile shifted slightly. Keep monitoring before triggering a retraining cycle.")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Current Anomaly Rate",
                f"{current_anomaly_rate:.1f}%",
                delta=f"{perf_data['rate_change_pct']:+.1f}% vs reference",
                help="Share of orders with at least one missing item in the current monitoring window."
            )
        with m2:
            st.metric(
                "Reference Baseline",
                f"{reference_anomaly_rate:.1f}%",
                help="Historical anomaly rate used as baseline for stability and drift comparison."
            )
        with m3:
            st.metric(
                "Features in Drift",
                f"{drifting_features}/{total_features}",
                help="Features flagged by KS-test with p-value < 0.05."
            )
        with m4:
            st.metric(
                "Next Scheduled Retrain",
                next_quarterly_date.strftime("%b %d"),
                delta=f"in {days_until_retraining} day(s)",
                help="Quarterly maintenance retraining schedule."
            )

        p1, p2, p3 = st.columns([1.0, 1.5, 1.2])

        with p1:
            col_p1_title, col_p1_help = st.columns([4, 1])
            with col_p1_title:
                st.markdown("**Anomaly Rate Stability**")
            with col_p1_help:
                st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)  # Spacer
                with st.popover("ℹ️"):
                    st.write("**Current vs Baseline** compares the current anomaly rate to the historical baseline to assess model stability.")
                    st.write("- **Current Anomaly Rate**: The percentage of anomalous predictions in the current monitoring window")
                    st.write("- **Reference Baseline**: Historical anomaly rate used for comparison")
                    st.write("- **Status**: Indicates if the model is stable or showing signs of degradation")
            
            plot_drift_card(
                "Current vs Baseline",
                current_val=current_anomaly_rate,
                ref_val=reference_anomaly_rate,
                status=perf_data['status']
            )

        with p2:
            render_feature_drift_table(drift_df)

        with p3:
            st.markdown("**Retraining Triggers**")
            trigger_performance = clean_rate_proxy < 80.0
            trigger_drift = drifting_features > 0
            trigger_schedule = days_until_retraining <= 14

            trigger_rows = [
                (
                    "Performance Clean < 80%",
                    f"Current: {clean_rate_proxy:.1f}%",
                    trigger_performance,
                    "Clean rate proxy is 100 - anomaly rate."
                ),
                (
                    "Data Drift > Threshold",
                    f"Drifting features: {drifting_features}",
                    trigger_drift,
                    "At least one monitored feature has p-value < 0.05."
                ),
                (
                    "Scheduled Quarterly",
                    f"Next: {next_quarterly_date.strftime('%b %d')}",
                    trigger_schedule,
                    "This trigger turns on when the scheduled retraining date is close."
                ),
            ]

            for label, detail, is_active, tooltip in trigger_rows:
                bg_color = "#FEE2E2" if is_active else "#ECFDF5"
                border_color = COLORS['critical'] if is_active else COLORS['success']
                icon = "⚠️" if is_active else "✅"
                status_txt = "Triggered" if is_active else "Normal"
                st.markdown(
                    f"""
                    <div title="{escape(tooltip)}" style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 0.7rem; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                            <span style="font-weight: 700; font-size: 0.88rem; color: #111827;">{label}</span>
                            <span style="font-size: 0.78rem; font-weight: 700; color: {border_color};">{icon} {status_txt}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #374151;">{detail}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


if __name__ == "__main__":
    main()
