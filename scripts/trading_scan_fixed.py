#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

now = datetime.now()
scan_key = now.strftime('%Y-%m-%dT%H:%M')
run_dir = Path('/Users/oymyisme/.openclaw/workspace/study/goji-btc-framework/data/runs') / now.strftime('%Y-%m-%d') / now.strftime('%H%M')
run_dir.mkdir(parents=True, exist_ok=True)

# latest manually extracted screenshot-mode values
price = 71538.9
funding_rate_display = '-0.0039%'
open_interest = '6.81B'
long_short_24h = '50.74% / 49.26%'
cvd_candles = '39.349K'
aggregated_spot_cvd = '9.288K'
funding_weighted_panel = '-0.0018'
oi_candles = '95.224K'
aggregated_futures_bid_ask_delta = '583.8124'

conclusion = '观望'
paper_trade_action = 'NONE'

result = {
    'scan_key': scan_key,
    'source': 'coinglass_screenshot_fixed_contract',
    'symbol': 'BTCUSDT',
    'exchange': 'Binance',
    'timeframe': '1H',
    'price': price,
    'funding_rate_display': funding_rate_display,
    'funding_weighted_panel': funding_weighted_panel,
    'open_interest': open_interest,
    'long_short_24h': long_short_24h,
    'cvd_candles': cvd_candles,
    'aggregated_spot_cvd': aggregated_spot_cvd,
    'oi_candles': oi_candles,
    'aggregated_futures_bid_ask_delta': aggregated_futures_bid_ask_delta,
    'conclusion': conclusion,
    'paper_trade_action': paper_trade_action,
    'screenshot_path': str(run_dir / 'screenshot.png'),
    'archive_dir': str(run_dir),
    'note': 'screenshot-mode fixed output; values currently fed from browser extraction step'
}

(run_dir / 'scan.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
(run_dir / 'scan.md').write_text('\n'.join([
    f"scan_key: {result['scan_key']}",
    f"symbol: {result['symbol']}",
    f"exchange: {result['exchange']}",
    f"timeframe: {result['timeframe']}",
    f"price: {result['price']}",
    f"funding_rate_display: {result['funding_rate_display']}",
    f"funding_weighted_panel: {result['funding_weighted_panel']}",
    f"open_interest: {result['open_interest']}",
    f"long_short_24h: {result['long_short_24h']}",
    f"cvd_candles: {result['cvd_candles']}",
    f"aggregated_spot_cvd: {result['aggregated_spot_cvd']}",
    f"oi_candles: {result['oi_candles']}",
    f"aggregated_futures_bid_ask_delta: {result['aggregated_futures_bid_ask_delta']}",
    f"conclusion: {result['conclusion']}",
    f"paper_trade_action: {result['paper_trade_action']}",
    f"archive_dir: {result['archive_dir']}",
]))

latest_path = Path('/Users/oymyisme/.openclaw/workspace/study/goji-btc-framework/data/latest_scan.json')
latest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

print(json.dumps(result, ensure_ascii=False, indent=2))
