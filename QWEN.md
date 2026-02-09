# Walmart Delivery Fraud Detection - QWEN.md

## Project Overview

This is a machine learning-powered fraud detection system for Walmart's delivery network in Central Florida. The system analyzes delivery data to identify patterns of fraud where customers report items as not received, determining whether responsibility lies with drivers, consumers, or systemic issues.

### Key Features
- **Fraud Detection Models**: Uses Isolation Forest, K-Means clustering, and DBSCAN for anomaly detection
- **Interactive Dashboard**: Built with Streamlit for data visualization and analysis
- **Risk Scoring System**: Assigns risk scores to drivers, customers, and orders
- **ETL Pipeline**: Processes multiple data sources (orders, customers, drivers, products, missing items)
- **Geographic Analysis**: Identifies fraud hotspots by location

### Technology Stack
- **Backend**: Python 3.11+
- **Database**: PostgreSQL
- **ML Frameworks**: Scikit-learn, MLflow
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Dashboard**: Streamlit
- **Data Processing**: Pandas, SQLAlchemy

## Project Structure

```
├── data/                   # Raw CSV data files
├── src/
│   ├── analysis/           # Statistical analysis modules
│   ├── config/             # Configuration and settings
│   ├── database/           # ORM models and SQL schemas
│   ├── etl/                # Data extraction, transformation, loading
│   ├── features/           # Feature engineering utilities
│   ├── models/             # ML model implementations
│   ├── reports/            # Report generation utilities
│   └── utils/              # General utility functions
├── dashboard/              # Streamlit dashboard application
├── notebooks/              # Jupyter notebooks for exploration
├── scripts/                # CLI scripts for setup and execution
├── docs/                   # Documentation
└── tests/                  # Unit and integration tests
```

## Data Sources

The system processes 5 main datasets:
- `orders.csv` - Order information (fact table)
- `customers_data.csv` - Customer profiles
- `drivers_data.csv` - Driver information
- `products_data.csv` - Product catalog
- `missing_items_data.csv` - Records of missing items

## Building and Running

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Required Python packages (see requirements.txt)

### Setup Instructions

1. **Install Dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

3. **Initialize Database**:
```bash
python scripts/setup_database.py
```

### Running the Application

1. **Start Dashboard**:
```bash
streamlit run dashboard/app.py
```
Access at http://localhost:8501

2. **Run Jupyter Notebooks**:
```bash
jupyter notebook notebooks/
```

3. **Train Models**:
```bash
python scripts/train_models.py
```

## Key Components

### Database Layer
- SQLAlchemy ORM models in `src/database/models.py`
- Schema definitions in `src/database/schemas.sql`
- Connection management in `src/config/database.py`

### ML Models
- Outlier detection with Isolation Forest (`src/models/outlier_detection.py`)
- Clustering algorithms for segmentation (`src/models/clustering.py`)
- Risk scoring system (`src/models/risk_scoring.py`)
- Model training pipeline (`src/models/train.py`)

### ETL Pipeline
- Data extraction from CSV files (`src/etl/extractors.py`)
- Data transformation and cleaning (`src/etl/transformers.py`)
- Database loading (`src/etl/loaders.py`)

### Dashboard Modules
- Overview: General metrics and trends
- Orders: Order analysis
- Drivers: Driver performance metrics
- Customers: Customer behavior analysis
- Fraud Detection: Risk score visualization
- Geographic: Regional analysis

## Development Conventions

- Follow PEP 8 style guidelines for Python code
- Use type hints for function parameters and return values
- Write unit tests for new functionality in the `tests/` directory
- Use MLflow for experiment tracking and model versioning
- Store configuration in environment variables via `.env` file
- Use logging instead of print statements for debugging

## Business Context

The system addresses a 15.02% order defect rate due to missing items, representing an estimated annual loss of $97,978 in Central Florida. Key focus areas include driver integrity (34% of active drivers associated with missing items), customer collusion detection, and identifying regional fraud hotspots.