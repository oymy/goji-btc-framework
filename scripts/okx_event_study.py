#!/usr/bin/env python3
import json
from pathlib import Path

candles_path = Path('data/raw/okx/candles_1h.json')
funding_path = Path('data/raw/okx/f funding.json')

if not candles_path.exists() or not funding_path.exists():
    print('missing okx data files')
    raise SystemExit(1)

candles = json.loads(candles_path.read_text())
funding = json.loads(funding_path.read_text())

rows = candles if isinstance(candles, list) else candles.get('data', [])
rows = list(reversed(rows))
closes = [float(r[4]) for r in rows]
ts = [int(r[0]) for r in rows]

fmap = {}
for item in funding.get('data', []):
    fmap[int(item['fundingTime'])] = float(item['fundingRate'])

signals = []
for i, t in enumerate(ts[:-24]):
    fr = fmap.get(t)
    if fr is None:
        continue
    if fr <= -0.0040:
        ret_24h = (closes[i+24] - closes[i]) / closes[i]
        signals.append((t, 'LONG', fr, ret_24h))
    elif fr >= 0.0040:
        ret_24h = (closes[i+24] - closes[i]) / closes[i]
        signals.append((t, 'SHORT', fr, ret_24h))

print(json.dumps({
    'signal_count': len(signals),
    'signals': signals[:20]
}, ensure_ascii=False, indent=2))
