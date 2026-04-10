#!/usr/bin/env python3
import json
import time
import urllib.request
from pathlib import Path

BASE = 'https://www.okx.com'
PROXY = 'http://127.0.0.1:7897'
INST = 'BTC-USDT-SWAP'
OUT = Path('data/raw/okx')
OUT.mkdir(parents=True, exist_ok=True)

proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)
opener.addheaders = [('User-Agent', 'Mozilla/5.0'), ('Accept', 'application/json')]
urllib.request.install_opener(opener)

def fetch(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

all_rows = []
after = None
for _ in range(30):
    url = f'{BASE}/api/v5/rubik/stat/contracts/open-interest-history?instId={INST}&period=1H'
    if after:
        url += f'&begin={after}'
    obj = fetch(url)
    data = obj.get('data', [])
    if not data:
        break
    all_rows.extend(data)
    after = data[-1][0]
    time.sleep(0.2)

(OUT / 'open_interest_history_1h.json').write_text(json.dumps(all_rows, ensure_ascii=False, indent=2))
print(json.dumps({'rows': len(all_rows)}, ensure_ascii=False, indent=2))
