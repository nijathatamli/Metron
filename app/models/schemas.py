"""Pydantic request / response schemas for the Metron API."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class Direction(str, Enum):
    """Metro travel direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CrowdLabel(str, Enum):
    """Human-readable crowd density label."""
    EMPTY = "empty"
    NORMAL = "normal"
    CROWDED = "crowded"
    PACKED = "packed"


class TransactionType(str, Enum):
    """Coin ledger transaction type."""
    EARN = "earn"
    SPEND = "spend"


class RedemptionStatus(str, Enum):
    """Partner redemption outcome."""
    SUCCESS = "success"
    FAILED = "failed"
    INSUFFICIENT_BALANCE = "insufficient_balance"


# ── Task 1 — Density ────────────────────────────────────────────────────────

class DensityRequest(BaseModel):
    """Input payload for the ML density prediction endpoint."""
    station_id: str = Field(..., examples=["IC-01"], description="Metro station code")
    timestamp: datetime = Field(..., examples=["2024-03-15T08:30:00"])
    direction: Direction = Field(..., examples=["inbound"])


class DensityResponse(BaseModel):
    """Output payload from the ML density prediction endpoint."""
    density_score: float = Field(..., ge=0.0, le=1.0, description="Predicted density 0–1")
    crowd_label: CrowdLabel
    cashback_percent: int = Field(..., ge=0, le=15, description="Cashback % for this density")
    optimal_travel_window: str = Field(..., description="Best low-density time window today")
    next_low_density_slot: str = Field(..., description="Next upcoming low-density time slot")


# ── Task 2 — Coin Engine ────────────────────────────────────────────────────

class EarnCoinsRequest(BaseModel):
    """Input for the coin-earning calculation."""
    trip_fare_azn: float = Field(..., gt=0, description="Trip fare in AZN")
    cashback_percent: int = Field(..., ge=0, le=15)


class EarnCoinsResponse(BaseModel):
    """Result of coin-earning calculation."""
    coins_earned: float = Field(..., ge=0)


class SpendCoinsResult(BaseModel):
    """Breakdown of a coin-spend operation."""
    coins_deducted: float = Field(..., ge=0)
    cash_paid: float = Field(..., ge=0)
    remaining_balance: float = Field(..., ge=0)


# ── Task 3 — Partner Redemption ─────────────────────────────────────────────

class RedeemRequest(BaseModel):
    """POST body for partner redemption."""
    user_id: uuid.UUID
    partner_id: uuid.UUID
    product_price_azn: float = Field(..., gt=0, description="Price of the product in AZN")
    coins_to_use: float = Field(..., ge=0, description="Coins the user wants to apply")
    idempotency_key: Optional[str] = Field(
        None, description="Client-supplied key to prevent duplicate transactions"
    )


class RedeemResponse(BaseModel):
    """Response returned after a successful partner redemption."""
    transaction_id: uuid.UUID
    coins_deducted: float
    cash_charged: float
    remaining_coin_balance: float
    partner_name: str
    status: RedemptionStatus
    timestamp: datetime
