#!/usr/bin/env python3
import json
from pathlib import Path

funding_path = Path('data/raw/okx/f funding.json')
funding = json.loads(funding_path.read_text())
vals = [float(x['fundingRate']) for x in funding.get('data', [])]
vals.sort()

summary = {
    'count': len(vals),
    'min': min(vals) if vals else None,
    'max': max(vals) if vals else None,
    'p10': vals[max(0, int(len(vals)*0.1)-1)] if vals else None,
    'p90': vals[min(len(vals)-1, int(len(vals)*0.9))] if vals else None,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
