"""
Business logic that sits between the ML model and the API layer.

Houses the cashback rules (pure function) and optimal-window calculation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple

from app.ml.model import predict_density
from app.models.schemas import CrowdLabel, DensityResponse


# ── Cashback rules (pure function) ──────────────────────────────────────────

def density_to_cashback(density: float) -> Tuple[int, CrowdLabel]:
    """
    Map a density score to a cashback percentage and crowd label.

    Thresholds (inclusive lower, exclusive upper):
        0.00–0.30 → 15 % (empty)
        0.30–0.60 →  8 % (normal)
        0.60–0.80 →  3 % (crowded)
        0.80–1.00 →  0 % (packed)

    Args:
        density: Float in [0.0, 1.0].

    Returns:
        (cashback_percent, crowd_label)
    """
    if density < 0.30:
        return 15, CrowdLabel.EMPTY
    if density < 0.60:
        return 8, CrowdLabel.NORMAL
    if density < 0.80:
        return 3, CrowdLabel.CROWDED
    return 0, CrowdLabel.PACKED


def _find_optimal_window(
    station_id: str,
    date: datetime,
    direction: str,
    window_hours: int = 2,
    step_minutes: int = 15,
) -> str:
    """
    Scan every `step_minutes` slot of `date` and return the contiguous
    `window_hours`-long block with the lowest average density.

    Returns a string like "11:00–13:00".
    """
    slots_per_window = (window_hours * 60) // step_minutes
    total_slots = (24 * 60) // step_minutes

    best_avg = 2.0  # higher than any possible score
    best_start = 0

    for start in range(total_slots - slots_per_window + 1):
        densities = []
        for offset in range(slots_per_window):
            slot_time = date.replace(hour=0, minute=0, second=0) + timedelta(
                minutes=(start + offset) * step_minutes
            )
            densities.append(predict_density(station_id, slot_time, direction))
        avg = sum(densities) / len(densities)
        if avg < best_avg:
            best_avg = avg
            best_start = start

    start_time = date.replace(hour=0, minute=0) + timedelta(
        minutes=best_start * step_minutes
    )
    end_time = start_time + timedelta(hours=window_hours)
    return f"{start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')}"


def _find_next_low_density_slot(
    station_id: str,
    current_ts: datetime,
    direction: str,
    threshold: float = 0.30,
    step_minutes: int = 15,
) -> str:
    """
    Starting from `current_ts`, walk forward in `step_minutes` increments
    and return the first slot whose density falls below `threshold`.

    Returns a time string like "10:45".
    """
    probe = current_ts
    # Look up to 24 h ahead
    end = current_ts + timedelta(hours=24)
    while probe <= end:
        score = predict_density(station_id, probe, direction)
        if score < threshold:
            return probe.strftime("%H:%M")
        probe += timedelta(minutes=step_minutes)
    return "N/A"


def get_density_prediction(
    station_id: str,
    timestamp: datetime,
    direction: str,
) -> DensityResponse:
    """
    Full density prediction pipeline: ML score → cashback rules → optimal window.

    Args:
        station_id: Metro station code (e.g. "IC-01").
        timestamp: Moment of the query.
        direction: "inbound" or "outbound".

    Returns:
        DensityResponse ready for serialisation.
    """
    density_score = predict_density(station_id, timestamp, direction)
    cashback_percent, crowd_label = density_to_cashback(density_score)

    optimal_window = _find_optimal_window(station_id, timestamp, direction)
    next_slot = _find_next_low_density_slot(station_id, timestamp, direction)

    return DensityResponse(
        density_score=density_score,
        crowd_label=crowd_label,
        cashback_percent=cashback_percent,
        optimal_travel_window=optimal_window,
        next_low_density_slot=next_slot,
    )
