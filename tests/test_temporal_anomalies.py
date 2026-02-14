import pandas as pd

from src.analysis.temporal import detect_temporal_anomalies


def test_detect_temporal_anomalies_default_threshold() -> None:
    """Regression: calling without threshold must not raise TypeError."""
    orders_df = pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "order_date": [
                "2023-01-10",
                "2023-01-17",
                "2023-01-24",
                "2023-02-07",
                "2023-02-14",
                "2023-02-21",
            ],
            "delivery_hour": [
                "09:00:00",
                "13:00:00",
                "18:00:00",
                "10:00:00",
                "15:00:00",
                "20:00:00",
            ],
            "driver_id": ["D1", "D2", "D1", "D3", "D2", "D3"],
            "customer_id": ["C1", "C2", "C3", "C1", "C2", "C4"],
            "order_amount": [100.0, 120.0, 90.0, 130.0, 110.0, 105.0],
            "items_delivered": [10, 9, 8, 9, 10, 7],
            "items_missing": [0, 1, 0, 2, 1, 3],
        }
    )

    anomalies = detect_temporal_anomalies(orders_df)

    assert set(anomalies.keys()) == {"monthly", "daily", "hourly"}
    assert all(isinstance(anomalies[key], list) for key in anomalies)
