#!/usr/bin/env python3
import json
from pathlib import Path

candles = json.loads(Path('data/raw/okx/candles_1h.json').read_text())
funding = json.loads(Path('data/raw/okx/f funding.json').read_text())
oi_rows = json.loads(Path('data/raw/okx/open_interest_history_1h.json').read_text())

candles = candles if isinstance(candles, list) else candles.get('data', [])
candles = list(reversed(candles))
closes = [float(r[4]) for r in candles]
ts = [int(r[0]) for r in candles]

fund_rows = sorted(funding.get('data', []), key=lambda x: int(x['fundingTime']))
fr_values = sorted(float(x['fundingRate']) for x in fund_rows)
low_th = fr_values[max(0, int(len(fr_values) * 0.1) - 1)]
high_th = fr_values[min(len(fr_values) - 1, int(len(fr_values) * 0.9))]
fmap = {int(x['fundingTime']): float(x['fundingRate']) for x in fund_rows}

# oi row format: [ts, oi, oiCcy, oiUsd]
oi_rows = sorted(oi_rows, key=lambda x: int(x[0]))
oimap = {int(x[0]): float(x[3]) for x in oi_rows}

def nearest_leq(mapping, t):
    keys = [k for k in mapping.keys() if k <= t]
    if not keys:
        return None
    return mapping[max(keys)]

aligned = []
for i, t in enumerate(ts):
    fr = nearest_leq(fmap, t)
    oi = nearest_leq(oimap, t)
    if fr is None or oi is None:
        continue
    aligned.append((i, t, fr, oi))

def future_ret(i, bars):
    if i + bars >= len(closes):
        return None
    return (closes[i + bars] - closes[i]) / closes[i]

longs, shorts = [], []
for idx in range(1, len(aligned)):
    i, t, fr, oi = aligned[idx]
    _, _, _, prev_oi = aligned[idx - 1]
    oi_change = (oi - prev_oi) / prev_oi if prev_oi else 0
    r24 = future_ret(i, 24)
    r4 = future_ret(i, 4)
    if r24 is None or r4 is None:
        continue

    if fr <= low_th and oi_change <= 0:
        longs.append((r4, r24, oi_change, fr))
    elif fr >= high_th and oi_change <= 0:
        shorts.append((r4, r24, oi_change, fr))

summary = {
    'low_threshold': low_th,
    'high_threshold': high_th,
    'long_count': len(longs),
    'short_count': len(shorts),
    'long_avg_4h': sum(x[0] for x in longs) / len(longs) if longs else None,
    'long_avg_24h': sum(x[1] for x in longs) / len(longs) if longs else None,
    'short_avg_4h_if_short': -(sum(x[0] for x in shorts) / len(shorts)) if shorts else None,
    'short_avg_24h_if_short': -(sum(x[1] for x in shorts) / len(shorts)) if shorts else None,
    'sample_longs': longs[:5],
    'sample_shorts': shorts[:5],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
