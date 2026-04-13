#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path

now = datetime.now()
base = Path('/Users/oymyisme/.openclaw/workspace/study/goji-btc-framework/data/runs') / now.strftime('%Y-%m-%d') / now.strftime('%H%M')
base.mkdir(parents=True, exist_ok=True)

payload = {
    'symbol': 'Binance BTCUSDT',
    'timeframe': '1H',
    'source': 'coinglass_screenshot',
    'status': 'manual-browser-assisted',
    'note': 'This script is a storage/output scaffold. Screenshot capture and value extraction are handled in browser-assisted flow.',
}

(base / 'scan.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))
(base / 'meta.json').write_text(json.dumps({
    'created_at': now.isoformat(),
    'archive_dir': str(base),
}, ensure_ascii=False, indent=2))
(base / 'scan.md').write_text('# trading-scan snapshot\n\nPending browser screenshot extraction.\n')

print(json.dumps({'archive_dir': str(base)}, ensure_ascii=False, indent=2))
