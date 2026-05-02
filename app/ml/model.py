"""
Density prediction model — trains on synthetic data and exposes an inference
function used by the FastAPI density endpoint.

The model is a GradientBoostingRegressor that predicts density_score from
(station one-hot, hour, day_of_week, is_weekend, direction).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder

from app.ml.training_data import STATIONS, generate_training_data

# ── Label encoders (fitted at module level for consistency) ──────────────────

_station_encoder = LabelEncoder()
_station_encoder.fit([s["station_id"] for s in STATIONS])

_direction_encoder = LabelEncoder()
_direction_encoder.fit(["inbound", "outbound"])

# ── Globals ──────────────────────────────────────────────────────────────────

_model: Optional[GradientBoostingRegressor] = None
_MODEL_PATH = os.getenv("ML_MODEL_PATH", "app/ml/density_model.joblib")


def _featurise(
    station_id: str,
    hour: float,
    day_of_week: int,
    is_weekend: int,
    direction: str,
) -> np.ndarray:
    """Convert raw inputs into a numeric feature vector."""
    station_enc = _station_encoder.transform([station_id])[0]
    direction_enc = _direction_encoder.transform([direction])[0]
    return np.array(
        [[station_enc, hour, day_of_week, is_weekend, direction_enc]],
        dtype=np.float64,
    )


def train_model(save_path: Optional[str] = None) -> GradientBoostingRegressor:
    """
    Train the density model on synthetic data and persist the artifact.

    Args:
        save_path: Where to write the .joblib file. Defaults to _MODEL_PATH.

    Returns:
        The trained model instance.
    """
    df = generate_training_data(days=30, seed=42)

    # Encode categorical columns
    df["station_enc"] = _station_encoder.transform(df["station_id"])
    df["direction_enc"] = _direction_encoder.transform(df["direction"])

    features = ["station_enc", "hour", "day_of_week", "is_weekend", "direction_enc"]
    X = df[features].values
    y = df["density_score"].values

    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X, y)

    path = save_path or _MODEL_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved → {path}")

    return model


def load_model(path: Optional[str] = None) -> GradientBoostingRegressor:
    """Load a persisted model from disk (trains on the fly if missing)."""
    global _model
    if _model is not None:
        return _model

    target = path or _MODEL_PATH
    if os.path.exists(target):
        _model = joblib.load(target)
    else:
        # First run — train and cache
        _model = train_model(save_path=target)
    return _model


def predict_density(
    station_id: str,
    timestamp: datetime,
    direction: str,
) -> float:
    """
    Predict the density score for a station / time / direction triple.

    Returns:
        A float clamped to [0.0, 1.0].
    """
    model = load_model()
    hour = timestamp.hour + timestamp.minute / 60.0
    day_of_week = timestamp.weekday()
    is_weekend = int(day_of_week >= 5)

    X = _featurise(station_id, hour, day_of_week, is_weekend, direction)
    raw: float = float(model.predict(X)[0])
    return round(float(np.clip(raw, 0.0, 1.0)), 4)


if __name__ == "__main__":
    train_model()
    # Quick smoke test
    ts = datetime(2024, 3, 15, 8, 30)
    for sid in ["IC-01", "MY-02", "HA-08"]:
        score = predict_density(sid, ts, "inbound")
        print(f"{sid}  {ts.isoformat()}  inbound → density={score}")
