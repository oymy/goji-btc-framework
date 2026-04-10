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
fr_values = [float(x['fundingRate']) for x in fund_rows]

if len(fr_values) < 20:
    raise SystemExit('not enough funding history')

low_idx = max(0, int(len(fr_values) * 0.1) - 1)
high_idx = min(len(fr_values) - 1, int(len(fr_values) * 0.9))
low_th = sorted(fr_values)[low_idx]
high_th = sorted(fr_values)[high_idx]

fmap = {int(item['fundingTime']): float(item['fundingRate']) for item in fund_rows}

def future_ret(i, bars):
    if i + bars >= len(closes):
        return None
    return (closes[i + bars] - closes[i]) / closes[i]

signals = []
for i, t in enumerate(ts):
    fr = fmap.get(t)
    if fr is None:
        continue
    r4 = future_ret(i, 4)
    r24 = future_ret(i, 24)
    if r4 is None or r24 is None:
        continue
    if fr <= low_th:
        signals.append({'ts': t, 'dir': 'LONG', 'fr': fr, 'ret_4h': r4, 'ret_24h': r24})
    elif fr >= high_th:
        signals.append({'ts': t, 'dir': 'SHORT', 'fr': fr, 'ret_4h': r4, 'ret_24h': r24})

longs = [x for x in signals if x['dir'] == 'LONG']
shorts = [x for x in signals if x['dir'] == 'SHORT']

summary = {
    'low_threshold': low_th,
    'high_threshold': high_th,
    'signal_count': len(signals),
    'long_count': len(longs),
    'short_count': len(shorts),
    'long_avg_ret_4h': sum(x['ret_4h'] for x in longs) / len(longs) if longs else None,
    'long_avg_ret_24h': sum(x['ret_24h'] for x in longs) / len(longs) if longs else None,
    'short_avg_ret_4h_raw': sum(x['ret_4h'] for x in shorts) / len(shorts) if shorts else None,
    'short_avg_ret_24h_raw': sum(x['ret_24h'] for x in shorts) / len(shorts) if shorts else None,
    'short_avg_ret_4h_if_short': -(sum(x['ret_4h'] for x in shorts) / len(shorts)) if shorts else None,
    'short_avg_ret_24h_if_short': -(sum(x['ret_24h'] for x in shorts) / len(shorts)) if shorts else None,
    'sample_signals': signals[:20],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
