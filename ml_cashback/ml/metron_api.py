"""
metron — inference API.

This is what your fullstack teammate will import in the website backend.

Usage:
    from metron_api import get_cashback

    result = get_cashback(station='Koroghlu', time_interval='07:30')
    # → {'station': 'Koroghlu', 'time_interval': '07:30-07:45',
    #    'cashback_%': 6.2, 'cashback_tier_%': 4, ...}

Optional kwargs:
    day_of_week  : 0=Mon ... 4=Fri  (default Wednesday=2)
    month        : 1-12              (default October=10)
"""
import pickle
from pathlib import Path
import numpy as np
import pandas as pd

# Load the model bundle once at import time
_BUNDLE_PATH = Path(__file__).parent / 'metron_model.pkl'
with open(_BUNDLE_PATH, 'rb') as f:
    _BUNDLE = pickle.load(f)

_MODEL    = _BUNDLE['model']
_D_MIN    = _BUNDLE['d_min']
_D_MAX    = _BUNDLE['d_max']
STATIONS  = _BUNDLE['stations']            # public — for dropdown lists


def _make_features(rows: pd.DataFrame) -> pd.DataFrame:
    """Same feature function used in training."""
    out = pd.DataFrame()
    out['station']     = rows['station'].values
    out['hour']        = rows['time_bin'].dt.hour.astype(np.int16).values
    out['minute']      = rows['time_bin'].dt.minute.astype(np.int16).values
    hd                 = out['hour'] + out['minute'] / 60.0
    out['hour_sin']    = np.sin(2 * np.pi * hd / 24)
    out['hour_cos']    = np.cos(2 * np.pi * hd / 24)
    out['day_of_week'] = rows['time_bin'].dt.dayofweek.astype(np.int8).values
    out['month']       = rows['time_bin'].dt.month.astype(np.int8).values
    return out


def _format_interval(h: int, m: int) -> str:
    end_m = m + 15
    end_h = h + (1 if end_m >= 60 else 0)
    end_m = end_m % 60
    return f'{h:02d}:{m:02d}-{end_h:02d}:{end_m:02d}'


def _cashback_from_demand(systemwide_pax: float) -> tuple:
    """Convert predicted system-wide passengers → (curve%, tier%)."""
    underuse = (_D_MAX - systemwide_pax) / (_D_MAX - _D_MIN)
    underuse = float(np.clip(underuse, 0.0, 1.0))
    curve = float(round(np.sqrt(underuse) * 12.0, 1))

    if   systemwide_pax <  800:  tier = 12
    elif systemwide_pax < 2500:  tier = 10
    elif systemwide_pax < 5000:  tier = 8
    elif systemwide_pax < 9000:  tier = 6
    elif systemwide_pax < 12000: tier = 4
    elif systemwide_pax < 15000: tier = 2
    else:                        tier = 0
    return curve, tier


def get_cashback(station: str, time_interval: str,
                 day_of_week: int = 2, month: int = 10) -> dict:
    """
    Compute cashback % for a station and 15-min time interval.

    Parameters
    ----------
    station       : str    e.g. "Koroghlu" — must be in STATIONS list.
    time_interval : str    "HH:MM" — start of the 15-min slot, e.g. "07:30".
    day_of_week   : int    0=Mon ... 4=Fri.  Default Wednesday.
    month         : int    1-12.             Default October.

    Returns
    -------
    dict with keys:
        station, time_interval, day_of_week,
        predicted_pax_at_station, predicted_pax_systemwide,
        cashback_%, cashback_tier_%
    """
    # --- validate inputs ---
    if station not in STATIONS:
        raise ValueError(f'Unknown station {station!r}. '
                         f'Must be one of: {STATIONS}')
    if not isinstance(time_interval, str) or ':' not in time_interval:
        raise ValueError(f'time_interval must be "HH:MM", got {time_interval!r}')
    try:
        h, m = map(int, time_interval.split(':'))
    except Exception:
        raise ValueError(f'time_interval must be "HH:MM", got {time_interval!r}')
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f'Invalid time {time_interval!r}')
    if day_of_week not in (0, 1, 2, 3, 4):
        raise ValueError(f'day_of_week must be 0..4 (Mon-Fri), got {day_of_week}')
    if not (1 <= month <= 12):
        raise ValueError(f'month must be 1..12, got {month}')

    # snap to 15-min grid
    m = (m // 15) * 15

    # build a synthetic timestamp with the requested dow/month
    base = pd.Timestamp(2025, month, 15, h, m)
    base = base + pd.Timedelta(days=(day_of_week - base.dayofweek) % 7)

    # predict passenger count at the requested station
    one = pd.DataFrame({'station': [station], 'time_bin': [base]})
    pax_station = float(_MODEL.predict(_make_features(one)).clip(min=0)[0])

    # predict system-wide demand (sum across all 27 stations) for cashback formula
    all_rows = pd.DataFrame({'station': STATIONS,
                             'time_bin': [base] * len(STATIONS)})
    pax_systemwide = float(_MODEL.predict(_make_features(all_rows)).clip(min=0).sum())

    # cashback
    cashback_pct, cashback_tier = _cashback_from_demand(pax_systemwide)

    return {
        'station'                  : station,
        'time_interval'            : _format_interval(h, m),
        'day_of_week'              : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'][day_of_week],
        'predicted_pax_at_station' : round(pax_station, 1),
        'predicted_pax_systemwide' : round(pax_systemwide, 0),
        'cashback_%'               : cashback_pct,
        'cashback_tier_%'          : cashback_tier,
    }


def list_stations() -> list:
    """Return the list of valid station names (for UI dropdowns)."""
    return list(STATIONS)


# Self-test on import — fail fast if the pickle is broken
if __name__ != '__main__':
    try:
        _ = get_cashback('Koroghlu', '08:00')
    except Exception as e:
        raise RuntimeError(f'metron_api failed self-test: {e}')
