"""
metron — train cashback model and save as pickle.

Fast model:  HistGradientBoostingRegressor (LightGBM-style, sklearn built-in).
Inputs:      station, time interval (e.g. '07:30'), day_of_week, month
Output:      cashback %  (0–12)

Run once:    python train_model.py
Produces:    metron_model.pkl
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

OUT = Path('/home/claude/analysis/metron_deploy')
OUT.mkdir(exist_ok=True)

# -----------------------------------------------------------------
# 1. LOAD DATA — Regime A weekdays only (where rush-hour exists)
# -----------------------------------------------------------------
print('Loading data...')
df = pd.read_csv('/home/claude/analysis/data.csv', parse_dates=['time_bin'])
df['dow'] = df.time_bin.dt.dayofweek
data = df[(df.time_bin < '2025-11-29') & (df.dow < 5) &
          (df.time_bin.dt.hour >= 6)].reset_index(drop=True).copy()
print(f'  {len(data):,} rows, {data.time_bin.dt.date.nunique()} weekdays')

# -----------------------------------------------------------------
# 2. FEATURES
# -----------------------------------------------------------------
def make_features(df_in: pd.DataFrame) -> pd.DataFrame:
    """Convert (station, time_bin) rows into model features."""
    out = pd.DataFrame()
    out['station']     = df_in['station'].values
    out['hour']        = df_in['time_bin'].dt.hour.astype(np.int16).values
    out['minute']      = df_in['time_bin'].dt.minute.astype(np.int16).values
    hd                 = out['hour'] + out['minute'] / 60.0
    out['hour_sin']    = np.sin(2 * np.pi * hd / 24)
    out['hour_cos']    = np.cos(2 * np.pi * hd / 24)
    out['day_of_week'] = df_in['time_bin'].dt.dayofweek.astype(np.int8).values
    out['month']       = df_in['time_bin'].dt.month.astype(np.int8).values
    return out

X = make_features(data)
y = data['passenger_count'].values

# -----------------------------------------------------------------
# 3. TRAIN/TEST SPLIT (time-based)
# -----------------------------------------------------------------
train_mask = (data['time_bin'] < '2025-10-01').values
test_mask  = ~train_mask
X_tr, y_tr = X.iloc[train_mask], y[train_mask]
X_te, y_te = X.iloc[test_mask],  y[test_mask]
print(f'  Train: {len(X_tr):,} (Jan–Sep 2025)   Test: {len(X_te):,} (Oct–Nov 2025)')

# -----------------------------------------------------------------
# 4. TRAIN
# -----------------------------------------------------------------
numeric = ['hour','minute','hour_sin','hour_cos','day_of_week','month']
pipe = Pipeline([
    ('prep', ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['station']),
        ('num', 'passthrough', numeric),
    ])),
    ('hgb', HistGradientBoostingRegressor(
        max_iter=300, max_depth=8, learning_rate=0.08, random_state=42)),
])
print('Training...')
pipe.fit(X_tr, y_tr)

# -----------------------------------------------------------------
# 5. EVAL
# -----------------------------------------------------------------
yhat = pipe.predict(X_te).clip(min=0)
mae = mean_absolute_error(y_te, yhat)
r2  = r2_score(y_te, yhat)
print(f'  MAE = {mae:.1f} pax    R² = {r2:.3f}')

# -----------------------------------------------------------------
# 6. CASHBACK CALIBRATION (from training data only)
# -----------------------------------------------------------------
A_tr = data.iloc[train_mask].copy()
A_tr['slot'] = A_tr['time_bin'].dt.strftime('%H:%M')
slot_pax = A_tr.groupby('slot')['passenger_count'].sum() / A_tr['time_bin'].dt.date.nunique()
D_MIN = float(slot_pax.min())
D_MAX = float(slot_pax.max())
STATIONS = sorted(data['station'].unique())
print(f'  D_MIN = {D_MIN:.0f}    D_MAX = {D_MAX:.0f}')

# -----------------------------------------------------------------
# 7. SAVE EVERYTHING NEEDED FOR INFERENCE
# -----------------------------------------------------------------
bundle = {
    'model'     : pipe,
    'd_min'     : D_MIN,
    'd_max'     : D_MAX,
    'stations'  : STATIONS,
    'metrics'   : {'MAE_test': float(mae), 'R2_test': float(r2)},
    'version'   : '1.0',
    'trained_on': 'Regime A weekdays (Jan – 28 Nov 2025), 06:00 onwards',
}
out_path = OUT / 'metron_model.pkl'
with open(out_path, 'wb') as f:
    pickle.dump(bundle, f)
print(f'\n✅  Saved → {out_path}  ({out_path.stat().st_size/1024:.1f} KB)')
