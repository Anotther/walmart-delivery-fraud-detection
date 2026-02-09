# PLAN-dashboard-streamlit

> **Goal**: Implement a comprehensive Streamlit dashboard for Walmart Delivery Fraud Detection, following the design and architecture defined in `dashboard/ANATOMY.md`.

## Context
The project requires a visual interface to display fraud detection metrics, alerts, and analysis. An anatomy document exists defining the visual identity (Walmart brand), data architecture, and sitemap. The backend data providers (`src.dashboard.data_cache`) and basic UI components (`src.dashboard.components`) already exist or are partially implemented. This plan focuses on assembling the full multi-page application.

## User Review Required
> [!NOTE]
> Please review the visual fidelity against the "HTML conceptual template" mentioned in the anatomy (if available). This plan assumes the `ANATOMY.md` description is the source of truth for design.

## Task Breakdown

### Phase 1: Foundation & Layout
- [ ] **Setup `dashboard/app.py`**:
    - Configure the main entry point with Streamlit page config.
    - Implement the custom Sidebar navigation (or use `streamlit-option-menu`).
    - Load global CSS styles.
- [ ] **Global Styling**:
    - [ ] Update/Create CSS in `dashboard/styles/` (or embedded) to match the new palette:
        - **Principal**: `#0053e2`
        - **Secondary**: `#003695`
        - **Third**: `#ffc220`
    - [ ] Ensure KPI cards and layout match the "Shadow/Rounded" specs.

### Phase 2: Core Components Integration
- [ ] **Review/Update `src.dashboard.components.py`**:
    - Ensure `kpi_card`, `plot_line_chart`, `plot_bar_chart` meet the visual specs.
    - Add any missing specific visual components (e.g., custom headers).

**Header Template (reuse on all pages)**:

```python
st.markdown("### Operational Intelligence")
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
    <div>
        <h1 style="margin:0; font-size: 2.5rem;">Page Title Here</h1>
        <p class="text-muted">One-line context aligned to the page scope.</p>
    </div>
    <div style="text-align: right;">
         <span class="badge badge-success">System Online</span>
    </div>
</div>
""", unsafe_allow_html=True)
```

### Phase 3: Page Implementation
Implement each page defined in the Sitemap, connecting to `src.dashboard.data_cache`.

#### 3.1 Overview (Home)
- [ ] Create `dashboard/pages/1_Overview.py`.
- [ ] Implement Hero Section.
- [ ] Integrate methods:
    - `get_overview_metrics()` for KPI cards.
    - `get_risk_alerts()` for active alerts count.
    - `get_temporal_trends()['monthly']` for the main chart.

#### 3.2 Real-time Monitor
- [ ] Create `dashboard/pages/2_Monitor.py`.
- [ ] Implement Risk Feed mechanism.
- [ ] Integrate methods:
    - `get_temporal_trends()['daily']`.
    - `get_risk_alerts(threshold=75)`.
    - `get_temporal_trends()['hourly']` (heatmap/bar).

#### 3.3 Driver Intelligence
- [ ] Create `dashboard/pages/3_Driver_Analysis.py`.
- [ ] Implement Driver Risk Distribution donut chart (`get_risk_distribution`).
- [ ] Implement Top 10 Suspects table (`get_top_suspicious`).
- [ ] Add filters for delivery count and score.

#### 3.4 Customer Intelligence
- [ ] Create `dashboard/pages/4_Customer_Analysis.py`.
- [ ] Implement Top 10 Suspicious Customers table.
- [ ] Implement Segmentation analytics.

#### 3.5 Geographic Intelligence
- [ ] Create `dashboard/pages/5_Geo_Analysis.py`.
- [ ] Implement Florida Heatmap using `get_regional_summary()`.
- [ ] Implement Regional Ranking table.

#### 3.6 Products & Losses
- [ ] Create `dashboard/pages/6_Product_Analysis.py`.
- [ ] Implement Top Missing Products table (`get_product_summary`).
- [ ] Implement Category Risk bar chart.

### Phase 4: Final Polish
- [ ] **Performance Check**: Ensure `data_cache` loading states are handled gracefully (spinners).
- [ ] **Navigation Check**: Ensure all pages link correctly and sidebar persists.

## Verification Plan

### Automated Tests
*   Run specific unit tests for data retrieval if available:
    *   `pytest tests/dashboard/test_data_cache.py` (if exists)

### Manual Verification
1.  **Launch Dashboard**: `streamlit run dashboard/app.py`
2.  **Navigation Walkthrough**: Click through all 6 pages in the sidebar.
3.  **Visual Check**:
    *   Verify colors match Walmart guidelines.
    *   Verify charts render without errors.
    *   Verify data populates in tables/cards (no empty states unless intended).
