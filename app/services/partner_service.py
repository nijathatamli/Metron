"""
Partner redemption business logic.

Handles coin-spend at partner merchants with idempotency and balance checks.
In a production deployment the DB calls would use real ORM queries; here we
use an in-memory store to keep the module self-contained and testable without
a running database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import HTTPException

from app.models.schemas import RedeemRequest, RedeemResponse, RedemptionStatus
from app.services.coin_engine import spend_coins

# ── In-memory stores (replaced by DB in production) ─────────────────────────

_user_balances: Dict[str, float] = {}
_partner_registry: Dict[str, dict] = {
    # Pre-seeded demo partners
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
        "name": "Coff Coffee",
        "category": "cafe",
        "is_active": True,
    },
    "b2c3d4e5-f6a7-8901-bcde-f12345678901": {
        "name": "Şirin Restoran",
        "category": "restaurant",
        "is_active": True,
    },
}
_idempotency_cache: Dict[str, RedeemResponse] = {}


def _get_user_balance(user_id: str) -> float:
    """Return current coin balance, defaulting to 10.0 for demo users."""
    return _user_balances.get(user_id, 10.0)


def _set_user_balance(user_id: str, balance: float) -> None:
    """Persist updated coin balance."""
    _user_balances[user_id] = round(balance, 2)


def process_redemption(req: RedeemRequest) -> RedeemResponse:
    """
    Execute a partner-redemption transaction.

    Steps:
      1. Check idempotency key — return cached response if already processed.
      2. Validate partner exists and is active.
      3. Validate user has sufficient coins for the requested amount.
      4. Compute spend breakdown via coin_engine.
      5. Debit user balance and return transaction receipt.

    Args:
        req: Validated RedeemRequest payload.

    Returns:
        RedeemResponse with full transaction details.

    Raises:
        HTTPException 409: Duplicate idempotency key (returns previous result).
        HTTPException 404: Unknown or inactive partner.
        HTTPException 400: coins_to_use exceeds user balance or product price.
    """
    # ── 1. Idempotency ──────────────────────────────────────────────────
    if req.idempotency_key and req.idempotency_key in _idempotency_cache:
        return _idempotency_cache[req.idempotency_key]

    # ── 2. Partner validation ───────────────────────────────────────────
    partner_id_str = str(req.partner_id)
    partner = _partner_registry.get(partner_id_str)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    if not partner["is_active"]:
        raise HTTPException(status_code=400, detail="Partner is currently inactive")

    # ── 3. Balance validation ───────────────────────────────────────────
    user_id_str = str(req.user_id)
    balance = _get_user_balance(user_id_str)

    if req.coins_to_use > balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coin balance. Available: {balance}",
        )
    if req.coins_to_use > req.product_price_azn:
        raise HTTPException(
            status_code=400,
            detail="coins_to_use cannot exceed product_price_azn",
        )

    # ── 4. Spend calculation ────────────────────────────────────────────
    # We pass coins_to_use as the "balance" so the engine deducts exactly
    # that amount (or less if price is lower).
    result = spend_coins(
        product_price_azn=req.product_price_azn,
        user_coin_balance=req.coins_to_use,
    )

    new_balance = round(balance - result["coins_deducted"], 2)
    _set_user_balance(user_id_str, new_balance)

    # ── 5. Build response ───────────────────────────────────────────────
    response = RedeemResponse(
        transaction_id=uuid.uuid4(),
        coins_deducted=result["coins_deducted"],
        cash_charged=result["cash_paid"],
        remaining_coin_balance=new_balance,
        partner_name=partner["name"],
        status=RedemptionStatus.SUCCESS,
        timestamp=datetime.now(timezone.utc),
    )

    # Cache for idempotency
    if req.idempotency_key:
        _idempotency_cache[req.idempotency_key] = response

    return response
