#!/usr/bin/env python3
import json
from pathlib import Path

candles_path = Path('data/raw/okx/candles_1h.json')
funding_path = Path('data/raw/okx/f funding.json')

candles = json.loads(candles_path.read_text())
funding = json.loads(funding_path.read_text())

rows = candles if isinstance(candles, list) else candles.get('data', [])
rows = list(reversed(rows))
closes = [float(r[4]) for r in rows]
ts = [int(r[0]) for r in rows]

fund_rows = sorted(funding.get('data', []), key=lambda x: int(x['fundingTime']))
fr_values = sorted(float(x['fundingRate']) for x in fund_rows)
fmap = {int(item['fundingTime']): float(item['fundingRate']) for item in fund_rows}

thresholds = [0.10, 0.05, 0.01]

def future_ret(i, bars):
    if i + bars >= len(closes):
        return None
    return (closes[i + bars] - closes[i]) / closes[i]

results = []
for tail in thresholds:
    n = len(fr_values)
    low_idx = max(0, int(n * tail) - 1)
    high_idx = min(n - 1, int(n * (1 - tail)))
    low_th = fr_values[low_idx]
    high_th = fr_values[high_idx]
    longs, shorts = [], []
    for i, t in enumerate(ts):
        fr = fmap.get(t)
        if fr is None:
            continue
        r4 = future_ret(i, 4)
        r24 = future_ret(i, 24)
        if r4 is None or r24 is None:
            continue
        if fr <= low_th:
            longs.append((r4, r24))
        elif fr >= high_th:
            shorts.append((r4, r24))
    results.append({
        'tail': tail,
        'low_threshold': low_th,
        'high_threshold': high_th,
        'long_count': len(longs),
        'short_count': len(shorts),
        'long_avg_4h': sum(x[0] for x in longs) / len(longs) if longs else None,
        'long_avg_24h': sum(x[1] for x in longs) / len(longs) if longs else None,
        'short_avg_4h_if_short': -(sum(x[0] for x in shorts) / len(shorts)) if shorts else None,
        'short_avg_24h_if_short': -(sum(x[1] for x in shorts) / len(shorts)) if shorts else None,
    })

print(json.dumps(results, ensure_ascii=False, indent=2))
