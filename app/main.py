"""
Metron API — FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings

# ── Globals ──────────────────────────────────────────────────────────────────
_coin_bundle = None
COIN_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "coin_model.pkl")

# Coin class → coin amount mapping (0=peak → 3=off-peak)
COIN_MAP = {0: 0, 1: 10, 2: 20, 3: 40}


def _load_coin_model():
    global _coin_bundle
    path = os.path.abspath(COIN_MODEL_PATH)
    _coin_bundle = joblib.load(path)
    print(f"✓ Loaded {_coin_bundle['model_name']} from {path}")
    print(f"  Stations: {len(_coin_bundle['valid_stations'])}")
    print(f"  Features: {len(_coin_bundle['feature_columns'])}")


def _predict_coins(station: str, hour: int, minute: int, month: int, dayofweek: int) -> int:
    """Run coin_model.pkl and return predicted coin class (0-3)."""
    if hour < 6:
        return 0  # metro closed

    # Round minute to nearest 15
    minute = (minute // 15) * 15
    is_weekend = 1 if dayofweek >= 5 else 0

    # Build feature row
    cols = _coin_bundle["feature_columns"]
    row = {c: 0 for c in cols}
    row["hour"] = hour
    row["minute"] = minute
    row["dayofweek"] = dayofweek
    row["is_weekend"] = is_weekend
    row["month"] = month

    # One-hot encode station (drop_first was used → first station "20 Yanvar" is dropped)
    station_col = f"station_{station}"
    if station_col in row:
        row[station_col] = 1

    df = pd.DataFrame([row])
    return int(_coin_bundle["model"].predict(df)[0])


# ── Lifespan — load model once ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_coin_model()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Smart City Metro Gamification — AI coin prediction",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Partner offers ───────────────────────────────────────────────────────────
PARTNER_OFFERS = [
    {"name": "Coffee Station", "icon": "☕", "category": "Coffee", "offer": "20% Discount for 15 min wait", "distance": "50m away", "min_wait": 0},
    {"name": "McDonald's", "icon": "🍔", "category": "Fast Food", "offer": "Free Tea with wait", "distance": "120m away", "min_wait": 10},
    {"name": "Baku Book Center", "icon": "📚", "category": "Bookstore", "offer": "Use Coins for entry", "distance": "200m away", "min_wait": 15},
    {"name": "Çörək Evi", "icon": "�", "category": "Bakery", "offer": "Pulsuz çay ilə", "distance": "80m away", "min_wait": 5},
    {"name": "Limon Lounge", "icon": "🍋", "category": "Cafe", "offer": "1+1 Latte", "distance": "150m away", "min_wait": 15},
    {"name": "Bravo Market", "icon": "🛒", "category": "Market", "offer": "3x coin bonus", "distance": "250m away", "min_wait": 20},
]


# ── Schemas ──────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    station: str = Field(..., description="Station name, e.g. '28-May'")
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    added_minutes: int = Field(0, ge=0, le=60)


class PartnerOut(BaseModel):
    name: str
    icon: str
    category: str
    offer: str
    distance: str


class PredictResponse(BaseModel):
    station: str
    time_now: str
    time_shifted: str
    coins_now: int
    coins_if_wait: int
    extra_coins: int
    coin_class_now: int
    coin_class_shifted: int
    added_minutes: int
    partners: List[PartnerOut]


# ── Predict Reward endpoint ──────────────────────────────────────────────────
@app.post("/predict-reward", response_model=PredictResponse, tags=["Reward"])
async def predict_reward(payload: PredictRequest):
    """
    Takes station + time + wait minutes.
    Uses coin_model.pkl to predict coin reward at now and after waiting.
    Returns coin difference + matching partner offers.
    """
    valid = _coin_bundle["valid_stations"]
    if payload.station not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown station. Valid: {valid}")

    now = datetime.now().replace(hour=payload.hour, minute=payload.minute, second=0)
    shifted = now + timedelta(minutes=payload.added_minutes)

    month = now.month
    dow = now.weekday()

    # Predict at current time
    cls_now = _predict_coins(payload.station, now.hour, now.minute, month, dow)
    coins_now = COIN_MAP[cls_now]

    # Predict at shifted time
    cls_shifted = _predict_coins(payload.station, shifted.hour, shifted.minute, month, dow)
    coins_shifted = COIN_MAP[cls_shifted]

    extra = coins_shifted - coins_now

    # Filter partners by wait time
    partners = [
        PartnerOut(name=p["name"], icon=p["icon"], category=p["category"],
                   offer=p["offer"], distance=p["distance"])
        for p in PARTNER_OFFERS
        if p["min_wait"] <= payload.added_minutes
    ]

    return PredictResponse(
        station=payload.station,
        time_now=now.strftime("%H:%M"),
        time_shifted=shifted.strftime("%H:%M"),
        coins_now=coins_now,
        coins_if_wait=coins_shifted,
        extra_coins=extra,
        coin_class_now=cls_now,
        coin_class_shifted=cls_shifted,
        added_minutes=payload.added_minutes,
        partners=partners,
    )


@app.get("/stations", tags=["Stations"])
async def list_stations():
    """Return valid station names for the dropdown."""
    return {"stations": _coin_bundle["valid_stations"]}


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.APP_VERSION}
