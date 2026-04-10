#!/usr/bin/env python3
import csv
import json
from pathlib import Path

base = Path('data/external/supervik')
rows = []

for path in sorted(base.glob('BTC-USDT_*_funding_history.csv')):
    exchange = path.name.split('_')[1]
    vals = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                vals.append(float(r['Funding Rate']))
            except Exception:
                pass
    vals.sort()
    if not vals:
        continue
    n = len(vals)
    summary = {
        'exchange': exchange,
        'count': n,
        'min': vals[0],
        'p01': vals[max(0, int(n*0.01)-1)],
        'p05': vals[max(0, int(n*0.05)-1)],
        'p10': vals[max(0, int(n*0.10)-1)],
        'median': vals[n//2],
        'p90': vals[min(n-1, int(n*0.90))],
        'p95': vals[min(n-1, int(n*0.95))],
        'p99': vals[min(n-1, int(n*0.99))],
        'max': vals[-1],
    }
    rows.append(summary)

print(json.dumps(rows, ensure_ascii=False, indent=2))
