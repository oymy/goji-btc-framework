#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTBOX = DATA / 'outbox'
OUTBOX.mkdir(parents=True, exist_ok=True)


def shanghai_now():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz)


def shanghai_now_str():
    return shanghai_now().strftime('%Y-%m-%d %H:%M CST')


def to_float(value):
    if value is None:
        return None
    s = str(value).strip().replace('%', '').replace(',', '')
    mult = 1.0
    if s.endswith('K'):
        mult = 1_000.0
        s = s[:-1]
    elif s.endswith('M'):
        mult = 1_000_000.0
        s = s[:-1]
    try:
        return float(s) * mult
    except Exception:
        return None


def arrow_from_delta(n):
    if n is None:
        return '→'
    if n > 0:
        return '↑'
    if n < 0:
        return '↓'
    return '→'


def describe_orderbook(n):
    if n is None:
        return '未知'
    if n > 0:
        return '买压偏强'
    if n < 0:
        return '卖压偏强'
    return '中性'


def load_previous_scan(current_scan_key: str):
    archive = DATA / 'archive' / 'scans.ndjson'
    if not archive.exists():
        return None
    rows = []
    for line in archive.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    rows = [r for r in rows if r.get('scan_key') != current_scan_key]
    return rows[-1] if rows else None


def analyze_framework(scan: dict, prev_scan=None) -> dict:
    fr = to_float(scan.get('funding_rate'))
    futures_cvd = to_float(scan.get('cvd_candles'))
    spot_cvd = to_float(scan.get('aggregated_spot_cvd'))
    oi = to_float(scan.get('open_interest'))
    orderbook = to_float(scan.get('aggregated_futures_bid_ask_delta'))

    prev_futures_cvd = to_float(prev_scan.get('cvd_candles')) if prev_scan else None
    prev_spot_cvd = to_float(prev_scan.get('aggregated_spot_cvd')) if prev_scan else None
    prev_oi = to_float(prev_scan.get('open_interest')) if prev_scan else None
    prev_price = to_float(prev_scan.get('price')) if prev_scan else None

    futures_cvd_delta = (futures_cvd - prev_futures_cvd) if futures_cvd is not None and prev_futures_cvd is not None else None
    spot_cvd_delta = (spot_cvd - prev_spot_cvd) if spot_cvd is not None and prev_spot_cvd is not None else None
    oi_delta = (oi - prev_oi) if oi is not None and prev_oi is not None else None
    price_delta = (to_float(scan.get('price')) - prev_price) if to_float(scan.get('price')) is not None and prev_price is not None else None

    conditions_long = 0
    conditions_short = 0

    if fr is not None and fr <= -0.0040:
        conditions_long += 1
    if fr is not None and fr >= 0.0040:
        conditions_short += 1

    if futures_cvd_delta is not None and futures_cvd_delta > 0:
        conditions_long += 1
    if futures_cvd_delta is not None and futures_cvd_delta < 0:
        conditions_short += 1

    if spot_cvd_delta is not None and spot_cvd_delta > 0:
        conditions_long += 1
    if spot_cvd_delta is not None and spot_cvd_delta < 0:
        conditions_short += 1

    if oi_delta is not None and oi_delta > 0:
        conditions_long += 1
        conditions_short += 1

    if orderbook is not None and orderbook > 0:
        conditions_long += 1
    if orderbook is not None and orderbook < 0:
        conditions_short += 1

    framework = '观望'
    if conditions_long >= 3 and conditions_long > conditions_short:
        framework = 'V1边缘 / 偏多'
    elif conditions_short >= 3 and conditions_short > conditions_long:
        framework = 'V1边缘 / 偏空'

    core_conflict = '五指标暂未形成明确一致性。'
    if orderbook is not None and spot_cvd is not None:
        if orderbook < 0 and spot_cvd > 0:
            core_conflict = '现货偏强，但订单簿卖压存在，信号分裂。'
        elif orderbook > 0 and spot_cvd < 0:
            core_conflict = '订单簿买压存在，但现货未确认，信号分裂。'
        elif orderbook > 0 and spot_cvd > 0:
            core_conflict = '现货与订单簿同向偏多。'
        elif orderbook < 0 and spot_cvd < 0:
            core_conflict = '现货与订单簿同向偏空。'

    conclusion = '观望'
    if '偏多' in framework:
        conclusion = '观望'
    elif '偏空' in framework:
        conclusion = '观望'

    return {
        'framework': framework,
        'signal_count': max(conditions_long, conditions_short),
        'direction_bias': 'LONG' if conditions_long > conditions_short else ('SHORT' if conditions_short > conditions_long else 'NONE'),
        'core_conflict': core_conflict,
        'conclusion': conclusion,
        'invalid_if': '若资金费率回到中性且现货/订单簿不同步，则继续观望。',
        'indicators': {
            'funding_rate': fr,
            'futures_cvd': futures_cvd,
            'spot_cvd': spot_cvd,
            'oi': oi,
            'orderbook': orderbook,
            'futures_cvd_delta': futures_cvd_delta,
            'spot_cvd_delta': spot_cvd_delta,
            'oi_delta': oi_delta,
            'price_delta': price_delta,
        }
    }


def format_summary(scan: dict, paper: dict, analysis: dict) -> str:
    indicators = analysis['indicators']
    lines = [
        f"BTC 监测 - {shanghai_now_str()}",
        "",
        f"框架：[{analysis['framework']}]",
        "",
        "五指标",
        f"1. 资金费率：{scan.get('funding_rate')}（{arrow_from_delta(indicators.get('funding_rate'))}，OI加权）",
        f"2. 合约 CVD：{scan.get('cvd_candles')}（{arrow_from_delta(indicators.get('futures_cvd_delta'))}，变化）",
        f"3. 现货 CVD：{scan.get('aggregated_spot_cvd')}（{arrow_from_delta(indicators.get('spot_cvd_delta'))}，变化）",
        f"4. OI：{scan.get('open_interest')}（{arrow_from_delta(indicators.get('oi_delta'))}）",
        f"5. 订单簿：{scan.get('aggregated_futures_bid_ask_delta')} BTC（{describe_orderbook(indicators.get('orderbook'))}）",
        "",
        f"信号：[{analysis['signal_count']}/5]",
        analysis['core_conflict'],
        "",
        f"结论：{analysis['conclusion']}",
        f"失效：{analysis['invalid_if']}",
        f"Price: {scan.get('price')}",
        f"Paper Action: {scan.get('paper_trade_action')}",
    ]
    if paper.get('status'):
        lines.append(f"Paper Engine: {paper.get('status')}")
    if paper.get('note'):
        lines.append(f"备注: {paper.get('note')}")
    lines.append('说明: 以浏览器DOM提取为主，OCR仅作兜底和交叉验证。')
    return '\n'.join(lines) + '\n'


capture = subprocess.run(
    ['node', str(ROOT / 'scripts' / 'trading_scan_screenshot.js')],
    capture_output=True,
    text=True,
    check=True,
)
scan = json.loads(capture.stdout)
prev_scan = load_previous_scan(scan.get('scan_key'))
analysis = analyze_framework(scan, prev_scan)
scan['conclusion'] = analysis['conclusion']
scan['framework'] = analysis['framework']

(DATA / 'latest_scan.json').write_text(json.dumps(scan, ensure_ascii=False, indent=2))

paper = subprocess.run(
    ['python3', str(ROOT / 'scripts' / 'paper_trade_engine.py')],
    capture_output=True,
    text=True,
    check=True,
)
paper_json = json.loads(paper.stdout)

summary = format_summary(scan, paper_json, analysis)
(OUTBOX / 'latest_summary.txt').write_text(summary)
(OUTBOX / f"summary-{scan['scan_key'].replace(':', '').replace('-', '').replace('T', '-')}.txt").write_text(summary)

result = {
    'scan': scan,
    'analysis': analysis,
    'paper_trade_engine': paper_json,
    'summary': summary,
    'summary_path': str(OUTBOX / 'latest_summary.txt'),
    'send_targets': {
        'discord': os.getenv('TRADING_SCAN_DISCORD_TARGET'),
        'wechat': os.getenv('TRADING_SCAN_WECHAT_TARGET'),
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
