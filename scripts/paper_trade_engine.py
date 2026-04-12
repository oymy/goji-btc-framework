#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'data'
account_path = BASE / 'paper_account.json'
trades_path = BASE / 'paper_trades.csv'
scan_path = BASE / 'latest_scan.json'

account = json.loads(account_path.read_text())
scan = json.loads(scan_path.read_text())
scan_key = scan['scan_key']
action = (scan.get('paper_trade_action') or 'NONE').upper()
price = scan.get('price')

if account.get('last_scan_key') == scan_key:
    print(json.dumps({'status': 'skip', 'reason': 'duplicate scan key', 'scan_key': scan_key}, ensure_ascii=False))
    raise SystemExit(0)

account['last_scan_key'] = scan_key
result = {'status': 'ok', 'scan_key': scan_key, 'action': action, 'mode': account.get('mode', 'manual-paper-trade')}

if not trades_path.exists():
    trades_path.write_text('trade_id,opened_at,source_job,direction,entry_price,position_usd,stop_loss,take_profit,status,closed_at,exit_price,pnl_usd,pnl_pct,note\n')

if action in {'LONG', 'SHORT'} and price is not None and not account.get('open_trade_id'):
    position_usd = round(float(account['current_balance_usd']) * float(account.get('position_size_pct', 0.2)), 2)
    trade_id = f"paper-{scan_key.replace(':', '').replace('-', '').replace('T', '-') }"
    row = {
        'trade_id': trade_id,
        'opened_at': datetime.now().isoformat(timespec='seconds'),
        'source_job': scan_key,
        'direction': action,
        'entry_price': price,
        'position_usd': position_usd,
        'stop_loss': '',
        'take_profit': '',
        'status': 'OPEN',
        'closed_at': '',
        'exit_price': '',
        'pnl_usd': '',
        'pnl_pct': '',
        'note': 'opened from latest_scan.json',
    }
    with trades_path.open('a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)
    account['open_trade_id'] = trade_id
    result['opened_trade_id'] = trade_id
elif action in {'LONG', 'SHORT'} and account.get('open_trade_id'):
    result['note'] = f"existing open trade {account['open_trade_id']}, skipped new entry"
else:
    result['note'] = 'no trade opened'

account_path.write_text(json.dumps(account, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False))
