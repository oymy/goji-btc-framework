#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')
ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / 'data' / 'runs'


def find_slot_dir(now: datetime) -> Path:
    source = now - timedelta(minutes=2)
    day_dir = RUNS_DIR / source.strftime('%Y-%m-%d')
    slot = source.strftime('%H%M')
    exact = day_dir / slot
    if exact.exists():
        return exact
    candidates = []
    if day_dir.exists():
        for p in day_dir.iterdir():
            if p.is_dir() and p.name.isdigit() and len(p.name) == 4 and p.name <= slot:
                candidates.append(p)
    if not candidates:
        raise FileNotFoundError(f'no run directory found for {source.strftime("%Y-%m-%d %H:%M")}')
    return sorted(candidates)[-1]


def main() -> None:
    now = datetime.now(TZ)
    run_dir = find_slot_dir(now)
    scan_json = run_dir / 'scan.json'
    if not scan_json.exists():
        raise FileNotFoundError(f'missing scan.json: {scan_json}')
    data = json.loads(scan_json.read_text())

    lines = [
        f"结论：{data.get('conclusion', '未知')}",
        '',
        f"- 时间：{data.get('scan_key', '未知')} Asia/Shanghai",
        f"- 价格：{data.get('price', '未知')}",
        f"- 资金费率：{data.get('funding_rate_display', '未知')}",
        f"- OI：{data.get('open_interest', '未知')}",
        f"- 24h 多空比：{data.get('long_short_24h', '未知')}",
        f"- 合约 CVD：{data.get('cvd_candles', '未知')}",
        f"- 现货 CVD：{data.get('aggregated_spot_cvd', '未知')}",
        f"- OI 加权资金面板：{data.get('funding_weighted_panel', '未知')}",
        f"- Futures B&A Delta：{data.get('aggregated_futures_bid_ask_delta', '未知')}",
        f"- 纸面动作：{data.get('paper_trade_action', 'NONE')}",
        '',
        f"截图：{data.get('screenshot_path', str(run_dir / 'screenshot.png'))}",
        f"归档：{data.get('archive_dir', str(run_dir))}",
    ]
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
