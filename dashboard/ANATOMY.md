# Dashboard Anatomy: Walmart Delivery Fraud Detection

This document defines the architecture, design system, and data flow for the Walmart Fraud Detection Dashboard. It serves as a reference for developers and stakeholders to understand the dashboard structure and implementation.

---

## Table of Contents

1. [Visual Identity & UX](#1-visual-identity--ux)
2. [Data Architecture](#2-data-architecture)
3. [Navigation Structure](#3-navigation-structure)
4. [Page Specifications](#4-page-specifications)
5. [Technical Implementation](#5-technical-implementation)
6. [Project Structure](#6-project-structure)

---

## 1. Visual Identity & UX

### Color Palette

**Brand Colors:**
- **Primary**: `#004C91` (Walmart Blue) - Headers, active sidebar, primary buttons
- **Secondary**: `#FFC220` (Walmart Yellow) - CTAs, highlights, accents
- **Accent**: `#0071CE` (Light Blue) - Hover states, gradients

**Semantic Colors:**
- **Critical**: `#EF4444` (Red) - High risk, critical alerts
- **Warning**: `#F59E0B` (Orange) - Medium risk, warnings
- **Success**: `#10B981` (Green) - Low risk, positive metrics
- **Background**: `#F8FAFC` (Gray-50) - Page background
- **Surface**: `#FFFFFF` - Card backgrounds

### Typography

- **Font Family**: Sans-serif (Inter, system-ui)
- **Headers**: Bold, larger sizes for hierarchy
- **Body**: Regular weight, comfortable reading size
- **Monospace**: Used for IDs and technical data

### Component Styling

- **Cards**: White background, subtle shadow (`shadow-lg`), rounded corners (`rounded-lg`)
- **Badges**: Color-coded by risk level, rounded pill shape
- **Tables**: Striped rows, hover effects, sortable columns
- **Charts**: Plotly interactive charts with Walmart color scheme

---

## 2. Data Architecture

### Backend Integration

The dashboard consumes processed data through a centralized caching layer:

**Source**: `src/dashboard/data_cache.py`
- **Class**: `DashboardCache`
- **Strategy**: LRU cache with 15-minute TTL
- **Refresh**: Manual refresh button available on all pages

### Data Source Abstraction

**Module**: `src/data_source/`
- **Factory Pattern**: `factory.py` determines CSV or PostgreSQL source
- **Interface**: `base.py` defines common data access methods
- **Implementations**:
  - `csv_source.py` - Direct CSV file reading (default for deployment)
  - `database_source.py` - PostgreSQL query-based access

### Cache Methods

Key data retrieval methods from `DashboardCache`:
- `get_overview_metrics()` - High-level KPIs
- `get_temporal_trends()` - Time-based patterns (monthly, weekly, hourly)
- `get_risk_distribution()` - Risk segmentation for drivers/customers
- `get_top_suspicious()` - High-risk entities
- `get_regional_summary()` - Geographic aggregations
- `get_product_summary()` - Product-level analysis
- `get_risk_alerts()` - Active fraud alerts
- `get_fraud_patterns()` - Statistical patterns and correlations

---

## 3. Navigation Structure

The dashboard is organized into **9 specialized pages**, accessible via sidebar navigation:

### Main Pages

1. **Home (app.py)** - Getting started guide and navigation overview
2. **Overview** - Executive summary and KPIs
3. **Monitor** - Real-time operational dashboard
4. **Drivers** - Driver risk analysis and profiling
5. **Customers** - Customer behavior and fraud indicators
6. **Geographic** - Regional hotspot analysis
7. **Product Analysis** - Product-level fraud patterns
8. **Methodology** - Model documentation and data quality
9. **Patterns** - Statistical fraud patterns
10. **Model Performance** - ML model monitoring (planned)

### Sidebar Component

**Implementation**: `src/dashboard/components.py` - `render_sidebar()`
- Fixed left sidebar with page icons
- Active page highlighting
- Walmart branding header
- Consistent across all pages

---

## 4. Page Specifications

### 4.1. Home (Entry Point)

**File**: `dashboard/app.py`

**Purpose**: Onboarding page to guide users through the dashboard modules

**Components**:
- Dashboard overview description
- Recommended navigation flow
- Module summaries (what each page provides)
- Data availability context (date range, alert threshold)

**Data**: Lightweight context via `get_home_context()`

---

### 4.2. Overview

**File**: `dashboard/pages/1_Overview.py`

**Purpose**: Executive-level KPIs and high-level fraud metrics

**Components**:
- **KPI Cards (Row 1)**:
  - Total Orders Analyzed
  - Missing Item Rate (%)
  - Estimated Fraud Cost ($)
  - Active High-Risk Alerts
- **Temporal Trends**:
  - Monthly fraud rate trend (line chart)
  - Weekly pattern analysis
- **Risk Distribution**:
  - Drivers by risk category (donut chart)
  - Customers by risk category (donut chart)
- **Geographic Heatmap**: Fraud concentration by region

**Data Sources**:
- `get_overview_metrics()`
- `get_temporal_trends()`
- `get_risk_distribution()`
- `get_regional_summary()`

---

### 4.3. Monitor

**File**: `dashboard/pages/2_Monitor.py`

**Purpose**: Operational dashboard for real-time fraud monitoring

**Components**:
- **System Status**: Last data refresh, uptime indicator
- **Daily KPIs**: Today's orders, fraud rate, alerts
- **Risk Alert Feed**:
  - Real-time scrollable list of high-risk entities
  - Filter by risk threshold (50-100)
  - Entity type, score, alert reason
  - "Investigate" action button
- **Hourly Pattern Chart**: Fraud incidents by hour of day
- **Recent Activity Timeline**: Latest suspicious events

**Data Sources**:
- `get_risk_alerts(threshold=75)`
- `get_temporal_trends()['hourly']`
- `get_daily_metrics()` (derived from temporal trends)

---

### 4.4. Drivers

**File**: `dashboard/pages/3_Drivers.py`

**Purpose**: Identify high-risk drivers and analyze delivery patterns

**Components**:
- **Risk Distribution**: Donut chart of drivers by risk level
- **Top 20 High-Risk Drivers Table**:
  - Driver ID, Total Trips, Missing Rate, Risk Score
  - Color-coded risk badges
  - Sortable columns
  - Behavioral flags (weekend spike, collusion indicator)
- **Filters**:
  - Minimum trips threshold
  - Minimum risk score
  - Risk category selector
- **Driver Profile Cards**: Detailed view for selected driver

**Data Sources**:
- `get_top_suspicious(n=20)['top_suspicious_drivers']`
- `get_risk_distribution()['driver_risk_distribution']`

---

### 4.5. Customers

**File**: `dashboard/pages/4_Customers.py`

**Purpose**: Identify fraudulent customer behavior patterns

**Components**:
- **Top 20 High-Risk Customers Table**:
  - Customer ID, Total Orders, Claim Rate, Risk Score
  - Order value vs claim frequency analysis
- **Customer Segmentation**:
  - Claim rate by order value bracket
  - Repeat offender identification
- **Suspicious Patterns**:
  - Multiple small claims pattern
  - High-value claim pattern
  - Driver-customer collusion indicators

**Data Sources**:
- `get_top_suspicious()['top_suspicious_customers']`
- `get_risk_distribution()['customer_risk_distribution']`

---

### 4.6. Geographic

**File**: `dashboard/pages/5_Geographic.py`

**Purpose**: Regional fraud hotspot identification and analysis

**Components**:
- **Florida Central Heatmap**:
  - Choropleth map colored by missing_rate
  - Cities: Winter Park, Altamonte Springs, Clermont, Apopka, Sanford
- **Regional Ranking Table**:
  - Region name, total orders, missing rate, estimated loss
  - Sorted by risk level
- **Regional Comparison Chart**: Bar chart of fraud rates by city

**Data Sources**:
- `get_regional_summary()`

**Visualization**: Plotly choropleth map

---

### 4.7. Product Analysis

**File**: `dashboard/pages/6_Product_Analysis.py`

**Purpose**: Identify high-risk products and categories

**Components**:
- **Top Missing Products Table**:
  - Product name, category, missing count, unit price, total loss
  - Sortable by any column
- **Category Risk Analysis**:
  - Bar chart of loss by category (Electronics, Grocery, etc.)
  - Missing rate by category
- **Price Range Analysis**: Correlation between price and missing rate
- **Product Anomaly Detection**: Products with unusually high missing rates

**Data Sources**:
- `get_product_summary()`

---

### 4.8. Methodology

**File**: `dashboard/pages/7_Methodology.py`

**Purpose**: Document analytical approach and data quality

**Components**:
- **Data Quality Metrics**:
  - Missing value rates
  - Data coverage by time period
  - Record counts per dataset
- **Model Documentation**:
  - Isolation Forest configuration
  - K-Means clustering approach
  - Risk scoring formula
- **Feature Engineering**:
  - Derived features explanation
  - Threshold definitions
- **Assumptions & Limitations**: Transparent methodology notes

**Data Sources**:
- Static documentation
- `get_data_quality_metrics()` (if available)

---

### 4.9. Patterns

**File**: `dashboard/pages/8_Patterns.py`

**Purpose**: Statistical fraud pattern analysis

**Components**:
- **Fraud Indicators**:
  - Temporal patterns (weekend spike, night deliveries)
  - Behavioral patterns (repeat offenders, collusion)
- **Statistical Tests Results**:
  - Correlation analysis (driver-customer relationships)
  - Anomaly thresholds
- **Pattern Visualization**:
  - Heatmaps showing correlations
  - Time series anomaly highlighting
- **Hypotheses & Findings**: Actionable insights from patterns

**Data Sources**:
- `get_fraud_patterns()`
- `get_correlation_analysis()`

---

### 4.10. Model Performance (Planned)

**File**: `dashboard/pages/9_Model_Performance.py`

**Purpose**: ML model monitoring and evaluation

**Components** (Planned):
- **Model Metrics**:
  - Precision, Recall, F1-Score
  - ROC-AUC curves
- **Drift Detection**: Feature distribution changes over time
- **Retraining Triggers**: Automated thresholds
- **MLflow Integration**: Link to experiment tracking

**Status**: Basic placeholder implemented

---

## 5. Technical Implementation

### Framework & Libraries

**Core**:
- **Streamlit 1.54** - Web framework
- **Python 3.11+** - Primary language
- **Pandas 2.2** - Data manipulation

**Visualization**:
- **Plotly 5.24** - Interactive charts
- **Matplotlib 3.9** - Statistical plots
- **Seaborn 0.13** - Enhanced visualizations

**Styling**:
- **Custom CSS** - `dashboard/styles/main.css` loaded via `load_css()`
- **streamlit-option-menu** - Sidebar navigation styling
- **Walmart Theme** - Configured in `.streamlit/config.toml`

### Component Architecture

**Reusable Components**: `dashboard/components/`
- `__init__.py` - Exports `load_css()`, `render_sidebar()`
- `charts.py` - Chart factory functions
- `filters.py` - Filter UI components
- `metrics.py` - KPI card components
- `tables.py` - Styled table components

### Caching Strategy

**Page-Level Caching**:
```python
@st.cache_data(ttl=900)  # 15 minutes
def get_page_data():
    cache = get_default_cache()
    return cache.get_overview_metrics()
```

**Benefits**:
- Reduced database/CSV load times
- Consistent data across page refreshes
- Manual refresh available via cache clear

---

## 6. Project Structure

### Complete File Tree

```
walmart-delivery-fraud-detection/
│
├── dashboard/                          # Streamlit Application
│   ├── app.py                         # Entry point (Home page)
│   ├── ANATOMY.md                     # This file
│   │
│   ├── pages/                         # Multi-page app modules
│   │   ├── 1_Overview.py             # Executive KPIs
│   │   ├── 2_Monitor.py              # Real-time monitoring
│   │   ├── 3_Drivers.py              # Driver analysis
│   │   ├── 4_Customers.py            # Customer analysis
│   │   ├── 5_Geographic.py           # Regional hotspots
│   │   ├── 6_Product_Analysis.py     # Product fraud patterns
│   │   ├── 7_Methodology.py          # Documentation
│   │   ├── 8_Patterns.py             # Statistical patterns
│   │   └── 9_Model_Performance.py    # ML monitoring
│   │
│   ├── components/                    # Reusable UI components
│   │   ├── __init__.py               # load_css(), render_sidebar()
│   │   ├── charts.py                 # Chart builders
│   │   ├── filters.py                # Filter widgets
│   │   ├── metrics.py                # KPI cards
│   │   └── tables.py                 # Styled tables
│   │
│   └── styles/                        # CSS styling
│       └── main.css                  # Walmart theme CSS
│
├── src/                               # Core Application Logic
│   ├── config/                       # Configuration modules
│   │   ├── settings.py               # Environment config
│   │   ├── risk_thresholds.py        # Risk scoring thresholds
│   │   └── database_manager.py       # DB connection pool
│   │
│   ├── data_source/                  # Data abstraction layer
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract interface
│   │   ├── csv_source.py             # CSV file reader
│   │   ├── database_source.py        # PostgreSQL reader
│   │   └── factory.py                # Source selection logic
│   │
│   ├── dashboard/                    # Dashboard data layer
│   │   ├── data_cache.py             # DashboardCache class
│   │   └── components.py             # UI component helpers
│   │
│   ├── database/                     # Database layer
│   │   ├── connection.py             # DB connection manager
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   └── sql/                      # SQL schema files
│   │
│   ├── etl/                          # ETL Pipeline
│   │   ├── extractors.py             # CSV extractors
│   │   ├── transformers.py           # Data transformations
│   │   └── loaders.py                # Database loaders
│   │
│   ├── features/                     # Feature Engineering
│   │   ├── order_features.py         # Order-level features
│   │   ├── driver_features.py        # Driver risk features
│   │   ├── customer_features.py      # Customer risk features
│   │   └── temporal_features.py      # Time-based features
│   │
│   ├── models/                       # ML Models
│   │   ├── base.py                   # Base model class
│   │   ├── outlier_detection.py      # Isolation Forest, LOF
│   │   ├── clustering.py             # K-Means, DBSCAN
│   │   ├── risk_scoring.py           # Risk score engine
│   │   ├── train.py                  # Training pipeline
│   │   └── predict.py                # Inference functions
│   │
│   ├── analysis/                     # Statistical Analysis
│   │   ├── fraud_patterns.py         # Pattern detection
│   │   ├── geographic.py             # Regional analysis
│   │   └── temporal.py               # Time series analysis
│   │
│   └── utils/                        # Utilities
│       ├── validators.py             # Data validation
│       └── logging_config.py         # Logging setup
│
├── data/                             # CSV Datasets
│   ├── orders.csv                    # Main transaction data
│   ├── customers_data.csv            # Customer profiles
│   ├── drivers_data.csv              # Driver information
│   ├── products_data.csv             # Product catalog
│   └── missing_items_data.csv        # Missing item reports
│
├── .streamlit/                       # Streamlit Configuration
│   ├── config.toml                   # Theme and server config
│   └── secrets.toml                  # Secret keys (not committed)
│
├── scripts/                          # CLI Tools
│   ├── setup_database.py             # Database initialization
│   ├── run_etl.py                    # ETL pipeline runner
│   ├── train_models.py               # Model training
│   └── validate_overview_page.py     # Page validation
│
├── tests/                            # Test Suite
│   ├── test_dashboard_pages_import.py
│   └── dashboard/                    # Dashboard-specific tests
│
├── requirements.txt                  # Python dependencies
├── packages.txt                      # System dependencies
├── DEPLOY.md                         # Deployment guide
├── README.md                         # Project overview
└── LICENSE                           # MIT License
```

---

## 7. Development Guidelines

### Adding a New Page

1. Create `dashboard/pages/N_PageName.py` (N = next number)
2. Import common components:
   ```python
   from src.dashboard.components import load_css, render_sidebar
   from src.dashboard.data_cache import get_default_cache
   ```
3. Set page config with Walmart theme
4. Implement page-specific caching function
5. Design layout using Streamlit columns/containers
6. Add page to this ANATOMY.md documentation

### Styling Guidelines

- Use CSS classes defined in `dashboard/styles/main.css`
- Follow Walmart color palette strictly
- Ensure responsive design (test on mobile)
- Maintain consistent spacing (Streamlit defaults)
- Use `unsafe_allow_html=True` only when necessary

### Performance Optimization

- Always use `@st.cache_data` for expensive operations
- Set appropriate TTL (900s = 15 min for most pages)
- Avoid repeated database calls within loops
- Use `st.spinner()` for long-running operations
- Implement pagination for large tables (>100 rows)

---

## 8. Future Enhancements

### Planned Features

- **User Authentication**: Login system with role-based access
- **Real-time Alerts**: Email/SMS notifications for critical fraud
- **Export Functionality**: Download reports as PDF/Excel
- **Model Retraining UI**: Interface for triggering model updates
- **A/B Testing Dashboard**: Evaluate fraud prevention measures
- **API Integration**: REST API for external systems

### Technical Debt

- Complete Model Performance page implementation
- Add comprehensive unit tests for all pages
- Implement end-to-end testing with Streamlit AppTest
- Add accessibility features (ARIA labels, keyboard navigation)
- Optimize large dataset handling (pagination, lazy loading)

---

## 9. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-30 | 1.0 | Initial architecture document |
| 2024-02-14 | 1.1 | Added data source abstraction layer |
| 2024-02-20 | 1.2 | Updated with 9-page structure and deployment readiness |

---

## Contact & Support

For questions about dashboard architecture or implementation:
- Review this ANATOMY.md
- Check `DEPLOY.md` for deployment issues
- See `README.md` for project overview
- Open an issue on GitHub

---

**Document Version**: 1.2
**Last Updated**: February 20, 2026
**Maintained By**: Project Team
