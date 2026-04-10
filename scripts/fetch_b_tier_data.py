#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path

URLS = {
    'binance_klines': 'https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=10',
    'binance_funding': 'https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=10',
    'binance_oi': 'https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=10',
    'bybit_funding': 'https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=10',
    'bybit_oi': 'https://api.bybit.com/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=1h&limit=10',
    'okx_funding': 'https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=10',
    'okx_oi': 'https://www.okx.com/api/v5/public/open-interest?instId=BTC-USDT-SWAP',
}

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json,text/plain,*/*',
}

outdir = Path('data/raw')
outdir.mkdir(parents=True, exist_ok=True)

results = {}
for name, url in URLS.items():
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode('utf-8')
        (outdir / f'{name}.json').write_text(text)
        results[name] = {'status': 'ok', 'bytes': len(text)}
    except Exception as e:
        results[name] = {'status': 'error', 'error': str(e)}

print(json.dumps(results, indent=2, ensure_ascii=False))
