---
slug: getting-started
category: getting-started
generatedAt: 2026-02-14T18:58:46.844Z
---

# How do I set up and run this project?

## Prerequisites
- Python 3.11+
- PostgreSQL 14+

## Installation
```bash
git clone <repository-url>
cd walmart-delivery-fraud-detection
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database Setup
```bash
cp .env.example .env
python scripts/setup_database.py
```

## Run Main Workflows
```bash
# ETL only
python scripts/run_etl.py

# Model training
python scripts/train_models.py

# Dashboard
streamlit run dashboard/app.py
```

## Quality Checks
```bash
pytest tests/
scripts/security_checks.sh
```
