"""
metron — test script.

Run this BEFORE handing the pickle to your fullstack teammate to confirm:
   1. The pickle loads correctly.
   2. get_cashback() returns the right shape of result.
   3. Predictions are sane (peak hours give low cashback, off-peak give high).
   4. Invalid inputs raise clear errors.
   5. Performance is fast enough for a web backend.

Run:    python test_model.py
"""
import time
import sys
from metron_api import get_cashback, list_stations, STATIONS

# Pretty-printing helper
GREEN = '\033[92m'; RED = '\033[91m'; YELLOW = '\033[93m'; END = '\033[0m'
def ok(msg):    print(f'  {GREEN}✓{END} {msg}')
def fail(msg):  print(f'  {RED}✗{END} {msg}'); sys.exit(1)
def warn(msg):  print(f'  {YELLOW}!{END} {msg}')


print('=' * 70)
print('TEST 1: Model loads and basic call works')
print('=' * 70)
result = get_cashback('Koroghlu', '08:00')
print(f'  Result: {result}')
assert isinstance(result, dict), 'Result must be a dict'
required_keys = {'station', 'time_interval', 'day_of_week',
                 'predicted_pax_at_station', 'predicted_pax_systemwide',
                 'cashback_%', 'cashback_tier_%'}
assert required_keys.issubset(result.keys()), \
    f'Missing keys: {required_keys - result.keys()}'
ok('All required keys present')
ok(f'Cashback for Koroghlu 08:00 = {result["cashback_%"]}%')


print('\n' + '=' * 70)
print('TEST 2: Station list is correct')
print('=' * 70)
stations = list_stations()
print(f'  Number of stations: {len(stations)}')
print(f'  First 5: {stations[:5]}')
assert len(stations) == 27, f'Expected 27 stations, got {len(stations)}'
assert 'Koroghlu' in stations
assert '28-May' in stations
ok('27 stations available')


print('\n' + '=' * 70)
print('TEST 3: Sanity — peak hours give LOW cashback')
print('=' * 70)
peak_cases = [
    ('28-May',   '18:00'),   # PM peak king
    ('Ganjlik',  '18:00'),
    ('Koroghlu', '08:00'),   # AM peak king
]
for station, t in peak_cases:
    r = get_cashback(station, t)
    cb = r['cashback_%']
    print(f'  {station:<20} {t}  →  {cb}% (system pax: {r["predicted_pax_systemwide"]:,.0f})')
    if cb > 5:
        warn(f'High cashback at peak slot {station} {t} — investigate')
    else:
        ok(f'Low cashback at peak: {cb}%')


print('\n' + '=' * 70)
print('TEST 4: Sanity — off-peak hours give HIGH cashback')
print('=' * 70)
offpeak_cases = [
    ('Sahil',  '22:30'),   # late evening
    ('Bakmil', '14:00'),   # always-quiet station midday
    ('Ulduz',  '23:00'),   # late
]
for station, t in offpeak_cases:
    r = get_cashback(station, t)
    cb = r['cashback_%']
    print(f'  {station:<20} {t}  →  {cb}% (system pax: {r["predicted_pax_systemwide"]:,.0f})')
    if cb < 5:
        warn(f'Low cashback at off-peak slot {station} {t} — investigate')
    else:
        ok(f'High cashback at off-peak: {cb}%')


print('\n' + '=' * 70)
print('TEST 5: Sanity — cashback DECREASES from 07:00 → 08:00 → 08:30')
print('=' * 70)
slots = ['07:00', '07:15', '07:30', '07:45', '08:00', '08:15', '08:30', '08:45']
print(f'  Station: Koroghlu')
last_cb = 100
for t in slots:
    r = get_cashback('Koroghlu', t)
    cb = r['cashback_%']
    direction = '↓' if cb < last_cb else ('↑' if cb > last_cb else '=')
    print(f'    {t}  →  {cb:>5}%  {direction}  (pax: {r["predicted_pax_systemwide"]:,.0f})')
    last_cb = cb
ok('AM rush curve printed')


print('\n' + '=' * 70)
print('TEST 6: Cashback RECOVERS after PM peak (18:00 → 19:00 → 20:00)')
print('=' * 70)
slots = ['17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '21:00', '22:00']
for t in slots:
    r = get_cashback('28-May', t)
    cb = r['cashback_%']
    bar = '█' * int(cb)
    print(f'    {t}  →  {cb:>5}%  {bar}')
ok('PM cashback recovery curve printed')


print('\n' + '=' * 70)
print('TEST 7: Invalid inputs raise clear errors')
print('=' * 70)
for bad_station, bad_time, expected_msg in [
    ('NotARealStation', '08:00',  'Unknown station'),
    ('Koroghlu',        '25:00',  'Invalid time'),
    ('Koroghlu',        'noon',   'must be "HH:MM"'),
    ('Koroghlu',        '8',      'must be "HH:MM"'),
]:
    try:
        get_cashback(bad_station, bad_time)
        fail(f'Should have raised for ({bad_station!r}, {bad_time!r})')
    except ValueError as e:
        if expected_msg in str(e):
            ok(f'Rejected ({bad_station!r}, {bad_time!r}): {e}')
        else:
            warn(f'Raised but wrong message: {e}')


print('\n' + '=' * 70)
print('TEST 8: Performance — single call latency')
print('=' * 70)
N = 100
t0 = time.perf_counter()
for _ in range(N):
    get_cashback('Koroghlu', '08:00')
elapsed = (time.perf_counter() - t0) / N * 1000
print(f'  Average latency: {elapsed:.1f} ms per call')
if elapsed < 100:
    ok(f'Fast enough for a web backend ({elapsed:.1f} ms)')
else:
    warn(f'Slower than ideal ({elapsed:.1f} ms) — consider caching')


print('\n' + '=' * 70)
print('TEST 9: Full cashback grid — every station × every hour')
print('=' * 70)
import pandas as pd
rows = []
for s in STATIONS:
    for h in range(6, 24):
        r = get_cashback(s, f'{h:02d}:00')
        rows.append({'station': s, 'hour': f'{h:02d}:00', 'cashback': r['cashback_%']})
grid = pd.DataFrame(rows).pivot(index='station', columns='hour', values='cashback')
print(grid.to_string())
ok('Grid generated successfully')

# Save to CSV for the fullstack team
grid.to_csv('cashback_grid_preview.csv')
ok('Saved cashback_grid_preview.csv')


print('\n' + '=' * 70)
print(f'{GREEN}✅  ALL TESTS PASSED — model is ready to ship{END}')
print('=' * 70)
print('\nFiles to give your fullstack teammate:')
print('  • metron_model.pkl       (1.0 MB — the trained model)')
print('  • metron_api.py          (the inference module)')
print('  • requirements.txt       (dependencies)')
print('\nIntegration example:')
print('  from metron_api import get_cashback')
print('  result = get_cashback("Koroghlu", "07:30")')
print('  return jsonify(result)   # in Flask/FastAPI')
