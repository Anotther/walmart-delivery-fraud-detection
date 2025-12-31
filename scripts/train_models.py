#!/usr/bin/env python3
"""
Model training script.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.train import train_all_models


def main():
    """Train all fraud detection models."""
    print("=" * 50)
    print("Walmart Fraud Detection - Model Training")
    print("=" * 50)

    models = train_all_models()

    print("\n" + "=" * 50)
    print("Training Summary")
    print("=" * 50)
    for name, model in models.items():
        print(f"  - {name}: Trained successfully")


if __name__ == "__main__":
    main()
