#!/usr/bin/env python3
import json
import urllib.request

PROXY = 'http://127.0.0.1:7897'
BASE = 'https://www.okx.com'
INST = 'BTC-USDT-SWAP'

proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)
opener.addheaders = [('User-Agent', 'Mozilla/5.0'), ('Accept', 'application/json')]
urllib.request.install_opener(opener)

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

fr = get(f'{BASE}/api/v5/public/funding-rate?instId={INST}')['data'][0]
oi = get(f'{BASE}/api/v5/public/open-interest?instId={INST}')['data'][0]
c = get(f'{BASE}/api/v5/market/history-candles?instId={INST}&bar=1H&limit=25')['data']
closes = list(reversed([float(x[4]) for x in c]))
last_price = closes[-1]
ret_1h = (closes[-1] - closes[-2]) / closes[-2]
ret_24h = (closes[-1] - closes[0]) / closes[0]
fr_val = float(fr['fundingRate'])

def classify(fr_val):
    if fr_val <= -0.00005:
        return 'V1_LONG_EDGE'
    if fr_val >= 0.00008:
        return 'V1_SHORT_EDGE'
    if abs(fr_val) <= 0.00001:
        return 'V2_NEUTRAL_ZONE'
    return 'WATCH'

state = classify(fr_val)
if state == 'WATCH':
    conclusion = '观望'
elif state == 'V2_NEUTRAL_ZONE':
    conclusion = 'V2环境观察中'
elif state == 'V1_LONG_EDGE':
    conclusion = 'V1做多边缘观察'
else:
    conclusion = 'V1做空边缘观察'

print(json.dumps({
    'symbol': INST,
    'price': last_price,
    'funding_rate': fr_val,
    'oi_usd': float(oi['oiUsd']),
    'ret_1h': ret_1h,
    'ret_24h': ret_24h,
    'state': state,
    'conclusion': conclusion,
    'note': 'OKX单所弱化版，不是原版CoinGlass全网聚合trading-scan'
}, ensure_ascii=False, indent=2))
