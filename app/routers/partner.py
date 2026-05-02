"""Router for partner redemption endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import RedeemRequest, RedeemResponse
from app.services.partner_service import process_redemption

router = APIRouter(prefix="/api/v1/partner", tags=["Partner"])


@router.post(
    "/redeem",
    response_model=RedeemResponse,
    summary="Redeem Metron Coins at a partner business",
)
async def redeem(payload: RedeemRequest) -> RedeemResponse:
    """
    Apply Metron Coins toward a partner product purchase.

    Supports partial and full coin payments. An optional ``idempotency_key``
    in the request body prevents duplicate transactions when the client
    retries the same request.
    """
    return process_redemption(payload)
