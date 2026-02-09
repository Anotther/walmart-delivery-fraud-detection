# Visualization Style Guide

## Walmart E-commerce Fraud Detection Project

This guide establishes standards for all data visualizations in notebooks, dashboards, and reports.

---

## Quick Reference

### Import the Theme

```python
from src.config.viz_theme import (
    PROJECT_THEME,
    REGION_COLORS,
    CATEGORY_COLORS,
    PRICE_SEGMENT_COLORS,
    get_highlight_colors,
    get_top_n_highlight_colors,
    apply_project_theme,
    get_label,
)
```

### Dashboard Header Template

Use the same header structure across dashboard pages for consistency (Overview, Monitor, Drivers).

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

### Risk Category Colors (ALWAYS use these)

| Category | Color | Hex |
|----------|-------|-----|
| Low | Green | `#28A745` |
| Medium | Yellow | `#FFC107` |
| High | Orange | `#FD7E14` |
| Critical | Red | `#DC3545` |

```python
# Usage
color_discrete_map=PROJECT_THEME['risk_colors']
```

---

## Core Principles

### 1. Consistency Over Creativity

- Use the **same colors** for the same concepts across all notebooks
- Risk categories, regions, and product categories have fixed color mappings
- Don't invent new color schemes per visualization

### 2. Highlight the Insight

- Use **neutral colors** for context data
- Use **highlight colors** only for the key finding
- One insight per chart - don't overload with multiple highlights

### 3. Always Include Units

- Axis labels MUST include units: `%`, `$`, `count`, etc.
- Use the `AXIS_LABELS` dictionary or `get_label()` function

### 4. Right Chart for the Data

| Data Type | Recommended Chart |
|-----------|-------------------|
| Comparison (few categories) | Horizontal bar chart |
| Comparison (binary) | Horizontal bar chart (NOT pie) |
| Distribution | Histogram or box plot |
| Trend over time | Line chart |
| Part of whole (≤4 parts) | Donut chart (if necessary) |
| Correlation matrix | Heatmap with divergent colormap |
| Geographic patterns | Choropleth or bar by region |

---

## Color Usage Rules

### DO: Use Categorical Colors for Categories

```python
# CORRECT: Discrete map for regions
fig = px.bar(
    data,
    x='missing_rate',
    y='region',
    color='region',
    color_discrete_map=REGION_COLORS,  # Fixed mapping
)
```

### DON'T: Use Continuous Scale for Categories

```python
# WRONG: Gradient for categorical data
fig = px.bar(
    data,
    x='missing_rate',
    y='region',
    color='missing_rate',  # Creates gradient on categories
    color_continuous_scale='Reds',  # DON'T DO THIS
)
```

### DO: Highlight Key Insights

```python
# CORRECT: Highlight the top item
colors = get_highlight_colors(data_sorted, highlight_index=-1)
fig = px.bar(
    data_sorted,
    color=colors,
    color_discrete_map="identity",  # Use colors as-is
)
```

### DON'T: Encode Multiple Variables in Color

```python
# WRONG: Position shows frequency, color shows price (competing)
fig = px.bar(
    products,
    x='times_missing',  # Frequency as position
    color='price',       # Price as color - TOO MUCH INFO
    color_continuous_scale='Reds',
)

# CORRECT: Use one visual channel, put secondary in hover
fig = px.bar(
    products,
    x='times_missing',
    color=highlight_colors,
    hover_data={'price': ':.2f'},  # Price in tooltip
)
```

---

## Chart-Specific Guidelines

### Bar Charts

```python
# Horizontal bar chart (preferred for comparisons)
fig = px.bar(
    data.sort_values('metric'),
    x='metric',
    y='category',
    orientation='h',
    title='Clear Title with Context',
    labels={'metric': 'Metric Name (%)', 'category': 'Category'},
    color=get_highlight_colors(data, -1),
    color_discrete_map="identity",
    text='metric',
)
fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig.update_layout(height=400, showlegend=False)
```

### Pie/Donut Charts

**Use sparingly - only for ≤4 categories**

```python
# Donut chart (if you must use pie)
fig = px.pie(
    data,
    values='count',
    names='category',
    hole=0.4,  # Makes it a donut
    color='category',
    color_discrete_map=PROJECT_THEME['risk_colors'],
)
fig.update_traces(
    textposition='outside',
    textinfo='percent+label',
)
```

**Better alternative: Horizontal bar**

```python
# Convert pie data to horizontal bar
fig = px.bar(
    data.sort_values('count'),
    x='count',
    y='category',
    orientation='h',
    text='count',
)
```

### Heatmaps

```python
# Correlation matrix (divergent, centered at 0)
fig = px.imshow(
    correlation_matrix,
    color_continuous_scale='RdBu_r',
    zmin=-1, zmax=1,  # Center at 0
    text_auto='.2f',
    labels={'color': 'Correlation'},
)
fig.update_layout(height=500)

# Frequency heatmap (sequential)
fig = px.imshow(
    frequency_matrix,
    color_continuous_scale='Blues',
    text_auto=True,
    labels={'color': 'Count'},
)
```

### Time Series

```python
# Line chart with markers
fig = px.line(
    data,
    x='date',
    y='value',
    title='Trend Over Time',
    labels={'value': 'Value ($)', 'date': 'Date'},
    markers=True,
)
fig.update_traces(
    line_width=PROJECT_THEME['line_width'],
    marker_size=PROJECT_THEME['marker_size'],
)

# Add reference line for average
avg = data['value'].mean()
fig.add_hline(
    y=avg,
    line_dash='dash',
    line_color='gray',
    annotation_text=f'Average: {avg:.1f}',
)
```

### Dual Axis Charts

```python
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Primary axis (bars)
fig.add_trace(
    go.Bar(x=data['month'], y=data['orders'], name='Orders'),
    secondary_y=False,
)

# Secondary axis (line)
fig.add_trace(
    go.Scatter(x=data['month'], y=data['rate'], name='Rate (%)',
               mode='lines+markers', line=dict(color='red')),
    secondary_y=True,
)

# Clear axis labels
fig.update_yaxes(title_text="Total Orders", secondary_y=False)
fig.update_yaxes(title_text="Missing Rate (%)", secondary_y=True)
```

---

## Accessibility Standards

### Color Blindness

The `PROJECT_THEME['categorical']` palette is colorblind-safe (Okabe-Ito).

**Testing**: Use [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/) before finalizing.

### Contrast

- Text on colored backgrounds must meet WCAG AA (4.5:1 ratio)
- Use [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Font Sizes

| Element | Size |
|---------|------|
| Title | 14pt |
| Axis Labels | 12pt |
| Tick Labels | 10pt |
| Annotations | 11pt |

---

## Applying the Theme

### Method 1: Apply to Individual Figure

```python
from src.config.viz_theme import apply_project_theme

fig = px.bar(...)
fig = apply_project_theme(fig)
fig.show()
```

### Method 2: Use Project Template

```python
from src.config.viz_theme import register_project_template
register_project_template()

# All figures will use the template
fig = px.bar(...)
fig.update_layout(template='walmart_fraud')
```

### Method 3: Set Default at Notebook Start

```python
import plotly.io as pio
from src.config.viz_theme import register_project_template

register_project_template()
pio.templates.default = 'walmart_fraud'
```

---

## Table Style (Dashboard)

Use the same visual pattern as **"Validação de Consistência dos Dados Exibidos"** for analytic tables that require structured reading.

### Visual Pattern

- White card container with 12px radius, light border, and subtle shadow
- Header bar (`title + subtitle`) with contextual KPI chips on the right
- Compact uppercase column headers, zebra rows, and centered values
- Consistent row spacing (`10px`) and neutral grayscale palette for readability

### Drivers Page Reference

- Reusable renderer: `dashboard/pages/3_Drivers.py` (`render_detail_table`)
- Applied in advanced analytics tables:
  - Cluster summary
  - Regression coefficients
  - Driver detailed ranking (top missing rate)

### Usage Guidance

- Prefer this style when tables are part of an explanatory narrative (not raw data dumps)
- Keep table width fixed and cap columns to 4-6 when possible
- Add KPI chips for quick context (example: `R²`, `RMSE`, `Clusters`)

---

## Common Mistakes to Avoid

| Mistake | Correction |
|---------|------------|
| Using continuous colorscale for categories | Use `color_discrete_map` with fixed colors |
| No units on axes | Always include %, $, count, etc. |
| Multiple pie charts for comparison | Use grouped/stacked bar charts |
| Rainbow default palette | Use `PROJECT_THEME['categorical']` |
| Encoding 2 quantitative variables in position + color | One variable per visual channel |
| Heatmap with too many cells (>50) | Filter to top N items |
| Missing legend for color meaning | Add colorbar_title or legend |
| Gauge without benchmark context | Add threshold annotations |

---

## Checklist Before Committing

- [ ] Uses `PROJECT_THEME['risk_colors']` for risk categories
- [ ] Uses `REGION_COLORS` for geographic data
- [ ] All axes have units in labels
- [ ] No continuous colorscale on categorical data
- [ ] Key insight is visually highlighted
- [ ] Chart type is appropriate for the data
- [ ] Font sizes follow standards
- [ ] Tested for colorblind accessibility
- [ ] `apply_project_theme()` or template applied

---

## Examples Gallery

See these notebooks for properly styled visualizations:

1. `notebooks/01_eda_orders.ipynb` - Distribution and comparison charts
2. `notebooks/03_fraud_analysis.ipynb` - Risk scoring visualizations
3. `notebooks/05_products_missing_items.ipynb` - Product analysis

---

*Last Updated: December 2025*
*Audited by: GraphStyleGuard*
