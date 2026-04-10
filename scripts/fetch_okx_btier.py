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

def fetch_candles(limit=100, rounds=30):
    all_rows = []
    after = None
    for _ in range(rounds):
        url = f'{BASE}/api/v5/market/history-candles?instId={INST}&bar=1H&limit={limit}'
        if after:
            url += f'&after={after}'
        data = fetch(url).get('data', [])
        if not data:
            break
        all_rows.extend(data)
        after = data[-1][0]
        time.sleep(0.2)
    return all_rows

payload = {
    'f funding': fetch(f'{BASE}/api/v5/public/funding-rate-history?instId={INST}&limit=100'),
    'open_interest': fetch(f'{BASE}/api/v5/public/open-interest?instId={INST}'),
    'candles_1h': fetch_candles(),
}

for k, v in payload.items():
    (OUT / f'{k}.json').write_text(json.dumps(v, ensure_ascii=False, indent=2))

print(json.dumps({k: (len(v.get('data', [])) if isinstance(v, dict) else len(v)) for k, v in payload.items()}, ensure_ascii=False, indent=2))
