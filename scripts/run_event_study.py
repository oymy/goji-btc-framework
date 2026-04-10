#!/usr/bin/env python3
"""
Placeholder for first-pass event study.
Needs real data under data/raw or processed datasets before it can run meaningfully.
"""

from pathlib import Path

required = [
    Path('data/raw/binance_klines.json'),
    Path('data/raw/binance_funding.json'),
    Path('data/raw/binance_oi.json'),
]

missing = [str(p) for p in required if not p.exists()]
if missing:
    print('Missing required data files:')
    for m in missing:
        print('-', m)
    raise SystemExit(1)

print('Data files present. Next step: implement parsing and signal generation.')
