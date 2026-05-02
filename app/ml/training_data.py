"""
Synthetic training-data generator for Baku Metro density prediction.

Generates realistic passenger-density patterns across 8 stations with:
  - Morning peak  07:30–09:30
  - Evening peak  17:30–19:30
  - Low-density midday and late-night windows
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd

# ── Station registry ─────────────────────────────────────────────────────────
# Each station has a code, display name, and a base traffic multiplier that
# reflects how busy it typically is relative to the network average.

STATIONS: list[dict[str, str | float]] = [
    {"station_id": "IC-01", "name": "İçərişəhər",        "base_traffic": 0.85},
    {"station_id": "MY-02", "name": "28 May",             "base_traffic": 0.95},
    {"station_id": "NN-03", "name": "Nəriman Nərimanov",  "base_traffic": 0.80},
    {"station_id": "BK-04", "name": "Bakmil",             "base_traffic": 0.60},
    {"station_id": "UL-05", "name": "Ulduz",              "base_traffic": 0.65},
    {"station_id": "KR-06", "name": "Koroğlu",            "base_traffic": 0.75},
    {"station_id": "QQ-07", "name": "Qara Qarayev",       "base_traffic": 0.70},
    {"station_id": "HA-08", "name": "Həzi Aslanov",       "base_traffic": 0.90},
]

STATION_ID_TO_NAME: dict[str, str] = {s["station_id"]: s["name"] for s in STATIONS}  # type: ignore[misc]


def _time_density_curve(hour: float, base_traffic: float) -> float:
    """
    Return a density score (0–1) for a given fractional hour of day.

    The curve is a sum of two Gaussians (morning + evening peaks) plus a
    small uniform floor, scaled by the station's base_traffic multiplier.
    """
    # Morning peak centred at 08:30, evening peak at 18:30
    morning = 0.9 * np.exp(-0.5 * ((hour - 8.5) / 0.8) ** 2)
    evening = 0.85 * np.exp(-0.5 * ((hour - 18.5) / 0.9) ** 2)
    floor = 0.10  # minimum off-peak density

    raw = (morning + evening + floor) * base_traffic
    # Add small random noise ±5 %
    noise = random.uniform(-0.05, 0.05)
    return float(np.clip(raw + noise, 0.0, 1.0))


def generate_training_data(
    days: int = 30,
    interval_minutes: int = 15,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a DataFrame of synthetic density observations.

    Args:
        days: Number of historical days to simulate.
        interval_minutes: Granularity of time slots.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns:
            station_id, station_name, timestamp, direction,
            hour, day_of_week, is_weekend, density_score
    """
    random.seed(seed)
    np.random.seed(seed)

    rows: list[dict] = []
    start_date = datetime(2024, 2, 1)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5  # Sat=5, Sun=6

        slots_per_day = (24 * 60) // interval_minutes
        for slot_idx in range(slots_per_day):
            ts = current_date + timedelta(minutes=slot_idx * interval_minutes)
            hour = ts.hour + ts.minute / 60.0

            for station in STATIONS:
                base: float = station["base_traffic"]  # type: ignore[assignment]
                # Weekends have ~40 % less traffic
                effective_base = base * 0.6 if is_weekend else base

                for direction in ("inbound", "outbound"):
                    # Inbound slightly higher during morning, outbound during evening
                    dir_mod = 1.0
                    if direction == "inbound" and 7 <= hour <= 10:
                        dir_mod = 1.10
                    elif direction == "outbound" and 17 <= hour <= 20:
                        dir_mod = 1.10

                    density = _time_density_curve(
                        hour, effective_base * dir_mod
                    )

                    rows.append(
                        {
                            "station_id": station["station_id"],
                            "station_name": station["name"],
                            "timestamp": ts.isoformat(),
                            "direction": direction,
                            "hour": round(hour, 2),
                            "day_of_week": current_date.weekday(),
                            "is_weekend": int(is_weekend),
                            "density_score": round(density, 4),
                        }
                    )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_training_data()
    print(f"Generated {len(df):,} rows across {df['station_id'].nunique()} stations")
    print(df.head(10))
    df.to_csv("training_data.csv", index=False)
    print("Saved → training_data.csv")
