"""
Application settings and configuration.
Loads environment variables and defines paths.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_PATH", BASE_DIR / "data"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_PATH", BASE_DIR / "outputs"))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "reports").mkdir(exist_ok=True)
(OUTPUT_DIR / "models").mkdir(exist_ok=True)
(OUTPUT_DIR / "plots").mkdir(exist_ok=True)

# Database settings
DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "walmart_fraud"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# SQLAlchemy connection string (password is URL-encoded to handle special chars)
DATABASE_URL = (
    f"postgresql://{DATABASE_CONFIG['user']}:{quote_plus(DATABASE_CONFIG['password'])}"
    f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
)

# Application settings
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
_debug_from_env = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
# Never allow debug mode in production, even if env var is misconfigured.
DEBUG = _debug_from_env and APP_ENV != "production"

# MLflow settings
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", str(BASE_DIR / "mlflow"))
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "walmart_fraud_detection")

# Data file paths
DATA_FILES = {
    "orders": DATA_DIR / "orders.csv",
    "customers": DATA_DIR / "customers_data.csv",
    "drivers": DATA_DIR / "drivers_data.csv",
    "products": DATA_DIR / "products_data.csv",
    "missing_items": DATA_DIR / "missing_items_data.csv",
}

# Central Florida regions in the dataset
REGIONS = [
    "Winter Park",
    "Altamonte Springs",
    "Clermont",
    "Apopka",
    "Sanford",
    "Orlando",
    "Kissimmee",
    "Lake Mary",
    "Oviedo",
    "Casselberry",
]
