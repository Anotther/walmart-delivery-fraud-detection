"""
Walmart Fraud Detection Dashboard - Entry Point
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dashboard.components import load_css, render_sidebar

st.set_page_config(
    page_title="Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Global CSS
load_css()
render_sidebar()

st.title("Walmart Fraud Detection System")
st.markdown("""
### Central Florida Fraud Control Tower

**Current Status**: 🔴 **CRITICAL ATTENTION REQUIRED**

> **Business Problem**: The delivery network is experiencing a **15.02% order defect rate** due to missing items, resulting in an estimated annual loss of **$97,978** in the Central Florida region alone.

#### Strategic Focus Areas
1.  **Driver Integrity**: 34% of active drivers are associated with missing items.
2.  **Customer Collusion**: Detecting repeated claims patterns.
3.  **Regional Hotspots**: Isolating high-risk delivery zones.

Select a module from the sidebar to begin investigation.
""")
