# Metron

> Cashback rewards platform for the Baku Metro — incentivises off-peak travel via density-based Metron Coin rewards.

## Architecture

```
app/
├── main.py                  # FastAPI entry point
├── config.py                # Environment-based settings
├── database.py              # Async SQLAlchemy engine
├── models/
│   └── schemas.py           # Pydantic request / response models
├── routers/
│   ├── density.py           # POST /api/v1/density/predict
│   └── partner.py           # POST /api/v1/partner/redeem
├── services/
│   ├── density_service.py   # Cashback rules & optimal-window logic
│   ├── coin_engine.py       # Earn / spend coin lifecycle
│   └── partner_service.py   # Redemption transaction handling
└── ml/
    ├── model.py             # GradientBoosting density model
    └── training_data.py     # Synthetic data generator (8 stations)

db/
└── schema.sql               # PostgreSQL tables, indexes, views
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Train the ML model ahead of time
python -m app.ml.model

# 3. Run the API
uvicorn app.main:app --reload

# 4. Open docs
open http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/density/predict` | Predict station density & cashback |
| `POST` | `/api/v1/partner/redeem` | Redeem coins at a partner business |
| `GET`  | `/health` | Liveness probe |

## Cashback Rules

| Density | Cashback | Label |
|---------|----------|-------|
| 0.00–0.30 | 15 % | empty |
| 0.30–0.60 | 8 % | normal |
| 0.60–0.80 | 3 % | crowded |
| 0.80–1.00 | 0 % | packed |

## Database

Apply the schema to a running PostgreSQL instance:

```bash
psql -U metron -d metron -f db/schema.sql
```

Tables: `users`, `metro_trips`, `coin_transactions`, `partners`, `redemptions`
View: `user_coin_summary`