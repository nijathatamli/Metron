# metron — cashback model

ML model that predicts subway cashback % based on station and time of day.

## Files

| File | Purpose |
|---|---|
| `metron_model.pkl` | Trained Gradient Boosting model (1.0 MB). Don't edit. |
| `metron_api.py` | Inference module — `import` this in the backend. |
| `train_model.py` | Re-train the model (only needed if data changes). |
| `test_model.py` | Test suite. Run before shipping. |
| `requirements.txt` | Python dependencies. |
| `cashback_grid_preview.csv` | Hour-by-station cashback table for sanity checks. |

## Setup

```bash
pip install -r requirements.txt
python test_model.py        # verify everything works
```

## Backend integration

```python
from metron_api import get_cashback, list_stations

# Get cashback for a transaction
result = get_cashback(station='Koroghlu', time_interval='07:30')
# → {
#     'station': 'Koroghlu',
#     'time_interval': '07:30-07:45',
#     'day_of_week': 'Wed',
#     'predicted_pax_at_station': 1456.0,
#     'predicted_pax_systemwide': 12792.0,
#     'cashback_%': 7.3,           # use this for the curve display
#     'cashback_tier_%': 6,         # use this for badge / UI tier
# }

# For dropdowns
stations = list_stations()  # → ['20 Yanvar', '28-May', ...] 27 items
```

### Flask example

```python
from flask import Flask, request, jsonify
from metron_api import get_cashback

app = Flask(__name__)

@app.route('/api/cashback')
def cashback():
    station = request.args.get('station')
    time = request.args.get('time')
    try:
        return jsonify(get_cashback(station, time))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

## Model performance

- **R² on test set**: 0.880 (model explains 88% of demand variance)
- **MAE**: 79 passengers per 15-min bin
- **Latency**: ~15 ms per call
- **Trained on**: Regime A weekdays, Jan – 28 Nov 2025, 06:00 onwards
- **Test set**: Oct – Nov 2025 (truly unseen)

## Notes

- `time_interval` is the **start** of a 15-min slot (`'07:30'` = 07:30–07:44).
  Minutes are auto-snapped to 15-min boundaries.
- `day_of_week` defaults to Wednesday; pass 0–4 (Mon–Fri) to override.
- Cashback is currently **time-based**, not station-based — same time gives
  same cashback at every station. This is intentional (fair, simple).
- The model only knows weekdays. Weekend/holiday queries will return
  weekday predictions.

## Re-training

If you get a fresh CSV:
1. Replace `data.csv` source path in `train_model.py`.
2. Run `python train_model.py`.
3. Run `python test_model.py` to verify.
