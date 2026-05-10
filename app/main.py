"""
Metron API — FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import math
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

# Subway fee factor used to compute reward percentage from predicted density
# reward_pct = round(100 - density_pct * SUBWAY_FEE_FACTOR)
SUBWAY_FEE_FACTOR = 0.6


def _load_coin_model():
    global _coin_bundle
    path = os.path.abspath(COIN_MODEL_PATH)
    _coin_bundle = joblib.load(path)
    print(f"Loaded {_coin_bundle['model_name']} from {path}")
    print(f"  Stations: {len(_coin_bundle['valid_stations'])}")
    print(f"  Features: {len(_coin_bundle['feature_columns'])}")


def _predict_reward_pct(station: str, hour: int, minute: int, month: int, dayofweek: int) -> float:
    """Predict density percentile then return bonus amount.

    Formula:
        reward_pct = 100 - density_pct * SUBWAY_FEE_FACTOR   (range ~40-100)
        bonus     = (reward_pct / 2) * SUBWAY_FEE_FACTOR / 100  (range ~0.12-0.30)
    """
    if hour < 6:
        return 0.0  # metro closed

    # Round minute to nearest 15
    minute = (minute // 15) * 15
    is_weekend = 1 if dayofweek >= 5 else 0

    cols = _coin_bundle["feature_columns"]
    row = {c: 0 for c in cols}
    row["hour"] = hour
    row["minute"] = minute
    if "is_weekend" in row:
        row["is_weekend"] = is_weekend

    station_col = f"station_{station}"
    if station_col in row:
        row[station_col] = 1

    df = pd.DataFrame([row])
    raw_density = float(_coin_bundle["model"].predict(df)[0])
    
    # Custom mapping to hit exact behavioral targets based on real 28-May densities:
    # 06:00 (d=5) -> 0.20
    # 07:30 (d=20) -> 0.16
    # 07:45 (d=24) -> 0.11
    # 08:00 (d=38) -> 0.05
    # 12:00 (d=46) -> 0.04
    # 18:00 (d=85) -> 0.01
    
    if raw_density <= 5.0:
        bonus = 0.20
    elif raw_density <= 20.0:
        # map 5..20 to 0.20..0.16
        bonus = 0.20 - (raw_density - 5.0) / 15.0 * 0.04
    elif raw_density <= 24.0:
        # cliff part 1: map 20..24 to 0.16..0.11
        bonus = 0.16 - (raw_density - 20.0) / 4.0 * 0.05
    elif raw_density <= 38.0:
        # cliff part 2: map 24..38 to 0.11..0.05
        bonus = 0.11 - (raw_density - 24.0) / 14.0 * 0.06
    elif raw_density <= 85.0:
        # long tail: map 38..85 to 0.05..0.01
        bonus = 0.05 - (raw_density - 38.0) / 47.0 * 0.04
    else:
        bonus = 0.01
        
    return round(bonus, 2)


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
    date: Optional[str] = Field(None, description="Optional date 'YYYY-MM-DD'. If omitted, today is used.")


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
    coins_now: float
    coins_if_wait: float
    extra_coins: float
    coin_class_now: float
    coin_class_shifted: float
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

    if payload.date:
        try:
            base_date = datetime.strptime(payload.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
        now = base_date.replace(hour=payload.hour, minute=payload.minute, second=0)
    else:
        now = datetime.now().replace(hour=payload.hour, minute=payload.minute, second=0)
    shifted = now + timedelta(minutes=payload.added_minutes)

    month = now.month
    dow = now.weekday()

    # Predict reward percentage at current time
    coins_now = _predict_reward_pct(payload.station, now.hour, now.minute, month, dow)
    cls_now = coins_now  # kept for schema compatibility

    # Predict reward percentage at shifted time
    coins_shifted = _predict_reward_pct(payload.station, shifted.hour, shifted.minute, month, dow)
    cls_shifted = coins_shifted

    extra = coins_shifted - coins_now

    # Always return all partners regardless of wait time
    partners = [
        PartnerOut(name=p["name"], icon=p["icon"], category=p["category"],
                   offer=p["offer"], distance=p["distance"])
        for p in PARTNER_OFFERS
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
