#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

capture = subprocess.run(
    ['node', str(ROOT / 'scripts' / 'trading_scan_screenshot.js')],
    capture_output=True,
    text=True,
    check=True,
)
scan = json.loads(capture.stdout)

paper = subprocess.run(
    ['python3', str(ROOT / 'scripts' / 'paper_trade_engine.py')],
    capture_output=True,
    text=True,
    check=True,
)

result = {
    'scan': scan,
    'paper_trade_engine': json.loads(paper.stdout),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
