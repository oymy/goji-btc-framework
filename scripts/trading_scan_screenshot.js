#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const http = require('http');

const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(ROOT, 'data');
const RUNS = path.join(DATA, 'runs');
const PAGE_URL = 'https://www.coinglass.com/tv/Binance_BTCUSDT';
const DEBUG_PORT = Number(process.env.OPENCLAW_CDP_PORT || 18800);

function nowParts() {
  const d = new Date();
  const z = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(d);
  const map = Object.fromEntries(z.filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
  return { date: `${map.year}-${map.month}-${map.day}`, hm: `${map.hour}${map.minute}`, iso: new Date().toISOString() };
}

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function httpReq(opts) {
  return new Promise((resolve, reject) => {
    const req = http.request(opts, res => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.end();
  });
}

function parseDomOverview(text) {
  const lines = String(text).split(/\n+/).map(s => s.trim()).filter(Boolean);
  const i = lines.indexOf('Overview');
  const out = {};
  if (i >= 0) {
    for (let p = i + 1; p + 1 < lines.length; p += 2) {
      const key = lines[p];
      const value = lines[p + 1];
      out[key] = value;
      if (key === 'Long/Short (24h)') break;
    }
  }
  const priceIdx = lines.findIndex(v => /^\d[\d,.]*$/.test(v) && lines[v.length] !== undefined);
  const match = text.match(/BTCUSDT\s+Binance\s+Long\s+Short\s+([\d.,]+)/s);
  out.price = match ? Number(match[1].replace(/,/g, '')) : null;
  out.funding_rate_display = out['Funding Rates'] || null;
  out.open_interest = out['Open Interest'] || null;
  out.long_short_24h = out['Long/Short (24h)'] || null;
  return out;
}

function normalizeOCRText(s) {
  return s.replace(/[|]/g, '').replace(/[Кк]/g, 'K').replace(/[Мм]/g, 'M').replace(/\s+/g, ' ').trim();
}

function pickValue(lines, { yMin, yMax, yTarget, pattern }) {
  const matches = lines
    .filter(l => l.x > 0.55 && l.y >= yMin && l.y <= yMax)
    .map(l => ({ ...l, normalized: normalizeOCRText(l.text) }))
    .filter(l => pattern.test(l.normalized))
    .sort((a, b) => Math.abs(a.y - yTarget) - Math.abs(b.y - yTarget));
  return matches[0]?.normalized || null;
}

async function main() {
  const t = nowParts();
  const runDir = path.join(RUNS, t.date, t.hm);
  ensureDir(runDir);

  const created = await httpReq({ host: '127.0.0.1', port: DEBUG_PORT, path: `/json/new?${encodeURIComponent(PAGE_URL)}`, method: 'PUT' });
  if (created.status !== 200) throw new Error(`cannot create tab on cdp port ${DEBUG_PORT}`);
  const page = JSON.parse(created.body);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0;
  const pending = new Map();
  const responses = [];
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++seq;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  ws.onmessage = event => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id).resolve(msg.result);
      pending.delete(msg.id);
      return;
    }
    if (msg.method === 'Network.responseReceived') {
      const { requestId, response } = msg.params;
      responses.push({ requestId, url: response.url, mimeType: response.mimeType });
    }
  };
  await new Promise(r => ws.onopen = r);
  await send('Network.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1200, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: PAGE_URL });
  await new Promise(r => setTimeout(r, 12000));

  const shot = await send('Page.captureScreenshot', { format: 'png' });
  const screenshotPath = path.join(runDir, 'screenshot.png');
  fs.writeFileSync(screenshotPath, Buffer.from(shot.data, 'base64'));

  const domText = (await send('Runtime.evaluate', { expression: 'document.body.innerText', returnByValue: true })).result.value;
  const ocrRaw = cp.execFileSync('swift', [path.join(__dirname, 'ocr_swift.swift'), screenshotPath], { encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 });
  const ocr = JSON.parse(ocrRaw);

  const overview = parseDomOverview(domText);
  const extracted = {
    price: overview.price,
    funding_rate_display: overview.funding_rate_display,
    open_interest: overview.open_interest,
    long_short_24h: overview.long_short_24h,
    cvd_candles: pickValue(ocr, { yMin: 0.60, yMax: 0.67, yTarget: 0.638, pattern: /^-?[\d.]+[KM]$/ }),
    aggregated_spot_cvd: pickValue(ocr, { yMin: 0.46, yMax: 0.52, yTarget: 0.489, pattern: /^-?[\d.]+[KM]$/ }),
    funding_weighted_panel: pickValue(ocr, { yMin: 0.33, yMax: 0.39, yTarget: 0.346, pattern: /^-?[\d.]+$/ }),
    oi_candles: pickValue(ocr, { yMin: 0.20, yMax: 0.26, yTarget: 0.226, pattern: /^-?[\d.]+[KM]$/ }),
    aggregated_futures_bid_ask_delta: pickValue(ocr, { yMin: 0.07, yMax: 0.13, yTarget: 0.096, pattern: /^-?[\d.]+$/ }),
  };

  const scanKey = `${t.date}T${t.hm.slice(0,2)}:${t.hm.slice(2)}`;
  const result = {
    scan_key: scanKey,
    source: 'coinglass_browser_cdp_ocr',
    symbol: 'BTCUSDT',
    exchange: 'Binance',
    timeframe: '1H',
    ...extracted,
    conclusion: '观望',
    paper_trade_action: 'NONE',
    screenshot_path: screenshotPath,
    archive_dir: runDir,
    page_url: PAGE_URL,
    captured_at: t.iso,
    status: Object.values(extracted).every(v => v !== null) ? 'ok' : 'partial',
    note: 'Price/FR/OI/LongShort from live DOM. Chart panel values from local screenshot OCR.'
  };

  fs.writeFileSync(path.join(runDir, 'ocr.json'), JSON.stringify(ocr, null, 2));
  fs.writeFileSync(path.join(runDir, 'meta.json'), JSON.stringify({ page_url: PAGE_URL, captured_at: t.iso, cdp_port: DEBUG_PORT, response_urls: responses.map(r => r.url).filter((v, i, a) => a.indexOf(v) === i) }, null, 2));
  fs.writeFileSync(path.join(runDir, 'scan.json'), JSON.stringify(result, null, 2));
  fs.writeFileSync(path.join(runDir, 'scan.md'), [
    `scan_key: ${result.scan_key}`,
    `price: ${result.price}`,
    `funding_rate_display: ${result.funding_rate_display}`,
    `open_interest: ${result.open_interest}`,
    `long_short_24h: ${result.long_short_24h}`,
    `cvd_candles: ${result.cvd_candles}`,
    `aggregated_spot_cvd: ${result.aggregated_spot_cvd}`,
    `funding_weighted_panel: ${result.funding_weighted_panel}`,
    `oi_candles: ${result.oi_candles}`,
    `aggregated_futures_bid_ask_delta: ${result.aggregated_futures_bid_ask_delta}`,
    `status: ${result.status}`,
    `archive_dir: ${result.archive_dir}`,
  ].join('\n') + '\n');
  fs.writeFileSync(path.join(DATA, 'latest_scan.json'), JSON.stringify(result, null, 2));
  ws.close();
  console.log(JSON.stringify(result, null, 2));
}

main().catch(err => {
  console.error(err.stack || String(err));
  process.exit(1);
});
