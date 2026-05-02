"""Router for ML density prediction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ml.training_data import STATION_ID_TO_NAME
from app.models.schemas import DensityRequest, DensityResponse
from app.services.density_service import get_density_prediction

router = APIRouter(prefix="/api/v1/density", tags=["Density"])


@router.post(
    "/predict",
    response_model=DensityResponse,
    summary="Predict station crowd density and cashback",
)
async def predict(payload: DensityRequest) -> DensityResponse:
    """
    Accepts a station / timestamp / direction triple and returns the predicted
    density score, crowd label, cashback percentage, and optimal travel windows.
    """
    if payload.station_id not in STATION_ID_TO_NAME:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown station_id '{payload.station_id}'. "
            f"Valid codes: {list(STATION_ID_TO_NAME.keys())}",
        )

    return get_density_prediction(
        station_id=payload.station_id,
        timestamp=payload.timestamp,
        direction=payload.direction.value,
    )
