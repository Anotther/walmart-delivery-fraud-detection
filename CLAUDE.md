# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data science project focused on detecting fraud in Walmart e-commerce deliveries in Central Florida. The project analyzes delivery data from 2023 to identify patterns and anomalies indicating potential fraud by drivers, customers, or systemic issues.

**Business Context**: Walmart faced $6.5 billion in theft losses in 2023, with 53% of the 2022-2023 increase coming from e-commerce deliveries where customers report missing items.

## Data Architecture

The project uses five primary CSV datasets:

### Core Data Files

1. **orders.csv** - Main transaction table
   - Primary key: `order_id` (unique per order)
   - Links to: `driver_id`, `customer_id`
   - Contains: order date, amount, region, items delivered/missing, delivery timestamp
   - Note: `order_amount` includes dollar sign and comma (e.g., "$1,095.54")

2. **missing_items_data.csv** - Products reported as not received
   - Primary key: `order_id`
   - Contains up to 3 product IDs per order (product_id_1, product_id_2, product_id_3)
   - Sparse structure: many orders have only 1-2 missing items
   - Links to: orders.csv via `order_id`, products_data.csv via product IDs

3. **drivers_data.csv** - Delivery driver information
   - Primary key: `driver_id` (format: WDID#####)
   - Contains: driver name, age, total trips in 2023
   - Links to: orders.csv via `driver_id`

4. **products_data.csv** - Product catalog
   - Primary key: `produc_id` (note: typo in column name, not "product_id")
   - Contains: product name, category, price (includes dollar sign)
   - Links to: missing_items_data.csv via product IDs

5. **customers_data.csv** - Customer information
   - Primary key: `customer_id` (format: WCID####)
   - Contains: customer name, age
   - Links to: orders.csv via `customer_id`

### Data Relationships

```
orders.csv (fact table)
├── driver_id → drivers_data.csv
├── customer_id → customers_data.csv
└── order_id → missing_items_data.csv
                └── product_id_* → products_data.csv
```

## Key Analysis Tasks

The project specification (in "Projeto de Data Science Detecção de Fraudes em Entregas do Walmart.md") outlines five main tasks:

1. **Exploratory Data Analysis (EDA)**: Understand data characteristics, handle missing values, identify unusual patterns by geography/driver/customer
2. **Fraud Pattern Detection**: Identify anomalous behavior using clustering/outlier analysis, correlate driver patterns with missing items
3. **Cause and Responsibility Assessment**: Determine if fraud is attributable to specific drivers, customers, regions, time periods, or product types
4. **Recommendations**: Propose preventive measures (photo verification, digital signatures, driver audits) with expected fraud reduction estimates
5. **Data Improvement Proposals**: Identify missing data that would improve fraud detection

## Project Deliverables

Expected outputs per the specification:
- Complete analysis report with insights, conclusions, and implementation feasibility
- Preventive measures recommendations
- Monitoring dashboard (Looker/Excel/Google Sheets/PowerBI)
- Enhancement proposals (A/B tests, additional data needs, customer/driver surveys)

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database (requires PostgreSQL running)
python scripts/setup_database.py

# Train ML models
python scripts/train_models.py

# Run dashboard
streamlit run dashboard/app.py

# Run tests
pytest tests/

# Run Jupyter notebooks
jupyter notebook notebooks/
```

## Project Structure

```
src/
├── config/          # Settings and database connection
├── database/        # ORM models and SQL schemas
├── etl/             # Extract, Transform, Load pipeline
├── features/        # Feature engineering modules
├── models/          # ML models (Isolation Forest, K-Means, etc.)
├── analysis/        # Statistical analysis modules
└── utils/           # Helper utilities

dashboard/           # Streamlit multi-page dashboard
notebooks/           # Jupyter notebooks for EDA
scripts/             # CLI scripts for setup and training
data/                # CSV data files
docs/                # Documentation
```

## Data Quality Notes

- **Price formatting**: Both `order_amount` and product `price` fields contain dollar signs and may contain commas
- **Column typo**: products_data.csv uses `produc_id` instead of `product_id`
- **Sparse data**: missing_items_data.csv has nullable product_id_2 and product_id_3 columns
- **Date range**: All data is from 2023 (January 1 - December 31)
- **Geographic scope**: Limited to Central Florida region (cities include Winter Park, Altamonte Springs, Clermont, Apopka, Sanford)

## Key Modules

### ETL Pipeline
- `src/etl/extractors.py`: Load CSV files
- `src/etl/transformers.py`: Clean and transform data (parse currency, dates)
- `src/etl/loaders.py`: Load into PostgreSQL

### Feature Engineering
- `src/features/order_features.py`: Order-level features (missing_rate, delivery_period)
- `src/features/driver_features.py`: Driver risk scoring
- `src/features/customer_features.py`: Customer risk scoring
- `src/features/temporal_features.py`: Time-based patterns

### ML Models
- `src/models/outlier_detection.py`: Isolation Forest, LOF
- `src/models/clustering.py`: K-Means, DBSCAN
- `src/models/risk_scoring.py`: Unified risk scoring engine

### Analysis
- `src/analysis/fraud_patterns.py`: Pattern detection and indicators
- `src/analysis/geographic.py`: Regional analysis
- `src/analysis/temporal.py`: Time-based analysis
