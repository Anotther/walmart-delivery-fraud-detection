# Dashboard Revision & Verification Plan

## Objective
Systematically verify every page in the dashboard to eliminate `NameError`, `ImportError`, and data availability crashes.

## Global Checks (All Files)
- [x] **Imports**: Verify `sys`, `Path` (from pathlib), `streamlit`.
- [ ] **Path Injection**: Ensure `sys.path.insert` is correctly pointing to the project root.
- [ ] **CSS Loading**: Verify `load_css()` is called after `st.set_page_config`.

## Page-Specific Checklists

### 1. `src/dashboard/components.py`
- [x] **FIX**: Add `from pathlib import Path` (Completed).
- [ ] **Verify**: Check `load_css` path resolution.

### 2. `dashboard/app.py` (Home)
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Components**: Verify `render_sidebar` call.

### 3. `dashboard/pages/1_Overview.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_overview_metrics` returns expected dict keys.
- [ ] **Viz**: Check `plot_line_chart` arguments match `components.py` signature.

### 4. `dashboard/pages/2_Monitor.py`
- [ ] **Imports**: Check `sys`, `Path`, `datetime`.
- [ ] **Data**: Verify `get_risk_alerts` and `get_temporal_trends`.
- [ ] **Viz**: Check `plot_bar_chart` columns (`hour` vs `hour_of_day`).

### 5. `dashboard/pages/3_Drivers.py`
- [ ] **Imports**: Check `sys`, `Path`, `plotly.graph_objects`.
- [ ] **Data**: Verify `get_driver_summary`.
- [ ] **Viz**: Check `risk_radar_chart` (uses `go.Figure`, needs `plotly.graph_objects`).

### 6. `dashboard/pages/4_Customers.py`
- [ ] **Imports**: Check `sys`, `Path`, `graphviz`.
- [ ] **Safety**: Verify `try-except` block for `graphviz`.
- [ ] **Data**: Verify `get_customer_summary`.

### 7. `dashboard/pages/5_Geographic.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_regional_summary`.
- [ ] **Viz**: Check `px.pie` and `px.bar` calls.

### 8. `dashboard/pages/6_Product_Analysis.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_product_summary`.

### 9. `dashboard/pages/7_Methodology.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_methodology_metadata`.

### 10. `dashboard/pages/8_Patterns.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_patterns_analysis`.

### 11. `dashboard/pages/9_Model_Performance.py`
- [ ] **Imports**: Check `sys`, `Path`.
- [ ] **Data**: Verify `get_model_performance_metrics`.
- [ ] **Logic**: Check `stats.ks_2samp` usage (requires `scipy`).

## Action Plan
1.  Run `py_compile` on all pages to catch syntax/import errors immediately.
2.  Manually inspect imports for each file identified above.
3.  Restart Streamlit server.
