"""
Trains a Random Forest regressor that predicts passenger density percentile
(0-100) for a given (station, hour, minute, dayofweek, is_weekend, month).

The main.py converts density_pct -> reward percentage using:
    reward_pct = 100 - density_pct * 0.6
(0.6 = subway fee factor)
"""

from __future__ import annotations

import os
import time

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "total_data_15min.csv")
MODEL_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "coin_model.pkl")


def train_and_save_model():
    print(f"Loading data from {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Missing {CSV_PATH}.")

    df = pd.read_csv(CSV_PATH)
    df['time_bin'] = pd.to_datetime(df['time_bin'])

    # Feature engineering
    df['hour'] = df['time_bin'].dt.hour
    df['minute'] = df['time_bin'].dt.minute
    df['is_weekend'] = df['time_bin'].dt.dayofweek.isin([5, 6]).astype(int)

    # Filter to operating hours (6 to 23)
    df = df[(df['hour'] >= 6) & (df['hour'] <= 23)].reset_index(drop=True)

    print("Computing density percentile per (station, is_weekend)...")
    # density_pct: percentile rank (0-100) of passenger_count within each station
    # split by weekend vs weekday so weekend mornings don't dilute weekday peaks
    df['density_pct'] = (
        df.groupby(['station', 'is_weekend'])['passenger_count']
          .rank(pct=True) * 100.0
    )

    print("Aggregating per (station, is_weekend, hour, minute) slot...")
    # average density across all dates for the same slot — sharp per-slot signal
    df = (df.groupby(['station', 'is_weekend', 'hour', 'minute'], as_index=False)
            ['density_pct'].mean())

    # Features and target — station/hour/minute/is_weekend
    features = ['station', 'hour', 'minute', 'is_weekend']
    X = df[features].copy()
    y = df['density_pct']

    print("One-hot encoding stations...")
    X = pd.get_dummies(X, columns=['station'], drop_first=True)

    valid_stations = sorted(df['station'].unique())

    # Train/test split for accuracy reporting
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = HistGradientBoostingRegressor(
        max_iter=600,
        max_depth=None,
        learning_rate=0.05,
        min_samples_leaf=3,
        l2_regularization=0.0,
        random_state=42,
    )

    print("Training HistGradientBoosting Regressor...")
    start_time = time.time()
    model.fit(X_train, y_train)
    print(f"Training complete in {time.time() - start_time:.2f}s")

    train_r2 = r2_score(y_train, model.predict(X_train))
    test_r2 = r2_score(y_test, model.predict(X_test))
    print(f"  R² train: {train_r2:.4f}")
    print(f"  R² test:  {test_r2:.4f}")

    bundle = {
        "model_name": "HistGradientBoosting Regressor (density %)",
        "model": model,
        "feature_columns": list(X.columns),
        "valid_stations": valid_stations,
        "r2_test": float(test_r2),
    }

    joblib.dump(bundle, MODEL_OUTPUT_PATH)
    print(f"Model successfully saved to {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train_and_save_model()
