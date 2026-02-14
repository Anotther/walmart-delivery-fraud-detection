# Dashboard Theme Accessibility Checklist

## Scope
- Theme modes: `Auto`, `Claro`, `Escuro`
- Device scope: `Desktop`
- Coverage: `dashboard/app.py` and pages `1` to `9`
- Accessibility target: `WCAG AA` for core text readability

## Global Acceptance Criteria
- [ ] Theme selector appears in sidebar and persists after navigation/reload.
- [ ] `Auto` mode follows Streamlit base theme (`theme.base`) with fallback to light.
- [ ] KPI cards remain legible in both modes.
- [ ] Tables keep readable headers, rows, and severity chips in both modes.
- [ ] Plotly charts keep readable titles, labels, legends, and hovers in both modes.
- [ ] No hardcoded `plot_bgcolor/paper_bgcolor = white` or `font_family = Inter` remains.

## Per-Page Manual Verification

### `dashboard/app.py`
- [ ] Header content readable in claro.
- [ ] Header content readable in escuro.
- [ ] Sidebar theme selector works and persists.

### `dashboard/pages/1_Overview.py`
- [ ] KPI cards and badges readable in claro.
- [ ] KPI cards and badges readable in escuro.
- [ ] Main charts readable in claro.
- [ ] Main charts readable in escuro.

### `dashboard/pages/2_Monitor.py`
- [ ] Drift table card readable in claro.
- [ ] Drift table card readable in escuro.
- [ ] Alerts feed and severity chips readable in claro.
- [ ] Alerts feed and severity chips readable in escuro.
- [ ] Charts readable in claro.
- [ ] Charts readable in escuro.

### `dashboard/pages/3_Drivers.py`
- [ ] Custom tables readable in claro.
- [ ] Custom tables readable in escuro.
- [ ] Relationship chips readable in claro.
- [ ] Relationship chips readable in escuro.
- [ ] Charts readable in claro.
- [ ] Charts readable in escuro.

### `dashboard/pages/4_Customers.py`
- [ ] Queue header and legend chips readable in claro.
- [ ] Queue header and legend chips readable in escuro.
- [ ] Case detail cards readable in claro.
- [ ] Case detail cards readable in escuro.
- [ ] Charts readable in claro.
- [ ] Charts readable in escuro.

### `dashboard/pages/5_Geographic.py`
- [ ] Geo table and chips readable in claro.
- [ ] Geo table and chips readable in escuro.
- [ ] Maps and charts readable in claro.
- [ ] Maps and charts readable in escuro.

### `dashboard/pages/6_Product_Analysis.py`
- [ ] Product header and pills readable in claro.
- [ ] Product header and pills readable in escuro.
- [ ] SKU queue and lineage cards readable in claro.
- [ ] SKU queue and lineage cards readable in escuro.
- [ ] Charts readable in claro.
- [ ] Charts readable in escuro.

### `dashboard/pages/7_Methodology.py`
- [ ] KPI cards readable in claro.
- [ ] KPI cards readable in escuro.
- [ ] Methodology charts readable in claro.
- [ ] Methodology charts readable in escuro.

### `dashboard/pages/8_Patterns.py`
- [ ] Behavior cards readable in claro.
- [ ] Behavior cards readable in escuro.
- [ ] Pattern charts readable in claro.
- [ ] Pattern charts readable in escuro.

### `dashboard/pages/9_Model_Performance.py`
- [ ] MLOps KPI and tables readable in claro.
- [ ] MLOps KPI and tables readable in escuro.
- [ ] MLOps charts readable in claro.
- [ ] MLOps charts readable in escuro.

## Evidence Log
- [ ] Add screenshots for both themes per critical page (`2`, `3`, `4`, `6`).
- [ ] Record any residual contrast issue and owner.
- [ ] Record final sign-off date and reviewer.
