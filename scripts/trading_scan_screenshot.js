#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const http = require('http');

const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(ROOT, 'data');
const RUNS = path.join(DATA, 'runs');
const ARCHIVE = path.join(DATA, 'archive');
const PAGE_URL = 'https://www.coinglass.com/tv/Binance_BTCUSDT';
const DEBUG_PORT = Number(process.env.OPENCLAW_CDP_PORT || 18800);
const CHROME_CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
];

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

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function isCdpReady() {
  try {
    const res = await httpReq({ host: '127.0.0.1', port: DEBUG_PORT, path: '/json/version', method: 'GET' });
    return res.status === 200;
  } catch {
    return false;
  }
}

function findChromeBinary() {
  return CHROME_CANDIDATES.find(p => fs.existsSync(p)) || null;
}

async function ensureCdpReady() {
  if (await isCdpReady()) return { ready: true, started: false };
  const chromeBin = findChromeBinary();
  if (!chromeBin) throw new Error(`cdp port ${DEBUG_PORT} not ready, and no Chrome binary found`);
  const userDataDir = `/tmp/goji-cdp-${DEBUG_PORT}`;
  ensureDir(userDataDir);
  const child = cp.spawn(chromeBin, [
    `--remote-debugging-port=${DEBUG_PORT}`,
    '--no-first-run',
    '--no-default-browser-check',
    `--user-data-dir=${userDataDir}`,
    'about:blank',
  ], { detached: true, stdio: 'ignore' });
  child.unref();
  for (let i = 0; i < 20; i++) {
    if (await isCdpReady()) return { ready: true, started: true, chromeBin };
    await sleep(500);
  }
  throw new Error(`cdp port ${DEBUG_PORT} not ready after auto-start attempt`);
}

function parseDomOverview(text) {
  const out = {};
  const compact = String(text).replace(/\r/g, '');
  const lines = String(text).split(/\n+/).map(s => s.trim()).filter(Boolean);

  const priceMatch = compact.match(/BTCUSDT\s+Binance\s+Long\s+Short\s+([\d.,]+)/s)
    || compact.match(/BTCUSDT\s+Binance[\s\S]*?([\d.,]+)\s*$/m);
  const frMatch = compact.match(/Funding Rates\s+([+-]?[\d.]+%)/s);
  const oiMatch = compact.match(/Open Interest\s+([\d.]+[BMK]?)/s);
  const lsMatch = compact.match(/Long\/Short \(24h\)\s+([\d.]+%\s*\/\s*[\d.]+%)/s);

  if (priceMatch) out.price = Number(priceMatch[1].replace(/,/g, ''));
  else {
    const priceLine = lines.find(v => /^\d[\d,.]*$/.test(v));
    out.price = priceLine ? Number(priceLine.replace(/,/g, '')) : null;
  }

  out.funding_rate_display = frMatch ? frMatch[1] : null;
  out.open_interest = oiMatch ? oiMatch[1] : null;
  out.long_short_24h = lsMatch ? lsMatch[1] : null;
  return out;
}

function normalizeOCRText(s) {
  return s.replace(/[|]/g, '').replace(/[Кк]/g, 'K').replace(/[Мм]/g, 'M').replace(/\s+/g, ' ').trim();
}

function pickValue(lines, { yMin, yMax, yTarget, pattern, xMin = 0.55, xMax = 1 }) {
  const matches = lines
    .filter(l => l.x >= xMin && l.x <= xMax && l.y >= yMin && l.y <= yMax)
    .map(l => ({ ...l, normalized: normalizeOCRText(l.text) }))
    .filter(l => pattern.test(l.normalized))
    .sort((a, b) => Math.abs(a.y - yTarget) - Math.abs(b.y - yTarget));
  return matches[0]?.normalized || null;
}

function pickNumericNearLabel(lines, { labelPattern, yTolerance = 0.04, xMin = 0.55, xMax = 1, valuePattern }) {
  const normalized = lines.map(l => ({ ...l, normalized: normalizeOCRText(l.text) }));
  const label = normalized.find(l => labelPattern.test(l.normalized));
  if (!label) return null;
  const candidates = normalized
    .filter(l => l.x >= xMin && l.x <= xMax && Math.abs(l.y - label.y) <= yTolerance)
    .filter(l => valuePattern.test(l.normalized))
    .sort((a, b) => Math.abs(a.x - label.x) - Math.abs(b.x - label.x));
  return candidates[0]?.normalized || null;
}

function parseScaledNumber(value) {
  if (!value) return null;
  const s = String(value).trim().toUpperCase();
  const m = s.match(/^(-?[\d.]+)([KM])?$/);
  if (!m) return null;
  const n = Number(m[1]);
  if (!Number.isFinite(n)) return null;
  const unit = m[2] || '';
  if (unit === 'K') return n * 1_000;
  if (unit === 'M') return n * 1_000_000;
  return n;
}

function validateBidAskDelta(value) {
  const n = parseScaledNumber(value);
  if (n === null) return null;
  if (Math.abs(n) > 10000) return null;
  return value;
}

async function fetchBtcPriceUsd() {
  try {
    const raw = cp.execFileSync('bash', ['-lc', 'HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"'], { encoding: 'utf8' });
    const data = JSON.parse(raw);
    const price = data?.bitcoin?.usd;
    return Number.isFinite(price) ? price : null;
  } catch {
    return null;
  }
}

function extractOverviewFromOCR(lines) {
  return {
    funding_rate_display: pickNumericNearLabel(lines, {
      labelPattern: /^Funding Rates$/i,
      yTolerance: 0.02,
      xMin: 0.82,
      xMax: 0.99,
      valuePattern: /^-?[\d.]+%?$/,
    }),
    open_interest: pickNumericNearLabel(lines, {
      labelPattern: /^Open Interest$/i,
      yTolerance: 0.02,
      xMin: 0.82,
      xMax: 0.99,
      valuePattern: /^[\d.]+[BMK]$/i,
    }),
    long_short_24h: pickNumericNearLabel(lines, {
      labelPattern: /^Long\/Short \(24h\)$/i,
      yTolerance: 0.02,
      xMin: 0.82,
      xMax: 0.99,
      valuePattern: /^\d{1,3}(?:\.\d+)?%\s*\/\s*\d{1,3}(?:\.\d+)?%$/,
    }),
  };
}

function extractStudyValueBlock(text, title, pattern) {
  const lines = String(text || '').split(/\n+/).map(s => s.trim()).filter(Boolean);
  const idx = lines.findIndex(l => l.includes(title));
  if (idx < 0) return [];
  const out = [];
  for (let i = idx + 1; i < Math.min(lines.length, idx + 8); i++) {
    const v = lines[i].replace(/−/g, '-');
    if (pattern.test(v)) out.push(v);
  }
  return out;
}

async function captureOverviewOCR(screenshotPath, overviewCropPath) {
  try {
    cp.execFileSync('python3', ['-c', `from PIL import Image\nimg=Image.open(r'''${screenshotPath}''')\nw,h=img.size\nleft=int(w*0.62)\ntop=int(h*0.00)\nright=int(w*0.995)\nbottom=int(h*0.12)\nimg.crop((left, top, right, bottom)).save(r'''${overviewCropPath}''')`], { stdio: 'ignore' });
  } catch {}
  const ocrRaw = cp.execFileSync('swift', [path.join(__dirname, 'ocr_swift.swift'), screenshotPath], { encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 });
  const ocr = JSON.parse(ocrRaw);
  return { ocr, overviewOCR: extractOverviewFromOCR(ocr) };
}

async function main() {
  const t = nowParts();
  const runDir = path.join(RUNS, t.date, t.hm);
  ensureDir(runDir);
  ensureDir(ARCHIVE);

  const cdp = await ensureCdpReady();
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
  const overviewCropPath = path.join(runDir, 'overview-crop.png');

  const domSnapshot = (await send('Runtime.evaluate', {
    expression: `(() => {
      const text = document.body.innerText || '';
      const lines = text.split(/\n+/).map(s => s.trim()).filter(Boolean);
      const idx = lines.indexOf('Overview');
      const overview = idx >= 0 ? lines.slice(idx, idx + 12) : [];
      const qsText = (selector) => {
        const el = document.querySelector(selector);
        return el ? (el.textContent || '').trim() : null;
      };
      const display = {
        funding_rate_display: qsText('.cg-fr-long2, .cg-fr-short2, .cg-fr-long, .cg-fr-short'),
        open_interest: qsText('.cg-oi, .open-interest, [class*="openInterest"], [class*="open-interest"]'),
        long_short_24h: (() => {
          const all = Array.from(document.querySelectorAll('div,span')).map(el => (el.textContent || '').trim()).filter(Boolean);
          return all.find(v => /^\d{1,3}(?:\.\d+)?%\s*\/\s*\d{1,3}(?:\.\d+)?%$/.test(v)) || null;
        })(),
      };
      return { text, overview, display };
    })()`,
    returnByValue: true
  })).result.value;
  const domText = domSnapshot?.text || '';
  const iframeText = (await send('Runtime.evaluate', {
    expression: `(() => {
      const frame = document.querySelector('iframe[id^="tradingview_"]');
      return frame?.contentDocument?.body?.innerText || null;
    })()`,
    returnByValue: true
  })).result.value;
  let { ocr, overviewOCR } = await captureOverviewOCR(screenshotPath, overviewCropPath);

  const overview = { ...parseDomOverview(domText), ...(domSnapshot?.display || {}) };
  if ((!overview.funding_rate_display || !overview.open_interest || !overview.long_short_24h) && domSnapshot?.overview?.length) {
    const ov = domSnapshot.overview;
    for (let i = 0; i < ov.length - 1; i++) {
      if (ov[i] === 'Funding Rates' && !overview.funding_rate_display) overview.funding_rate_display = ov[i + 1] || null;
      if (ov[i] === 'Open Interest' && !overview.open_interest) overview.open_interest = ov[i + 1] || null;
      if (ov[i] === 'Long/Short (24h)' && !overview.long_short_24h) overview.long_short_24h = ov[i + 1] || null;
    }
  }

  if (!overviewOCR.funding_rate_display || !overviewOCR.open_interest || !overviewOCR.long_short_24h) {
    await sleep(2500);
    const retryShot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(screenshotPath, Buffer.from(retryShot.data, 'base64'));
    const retried = await captureOverviewOCR(screenshotPath, overviewCropPath);
    if (!overviewOCR.funding_rate_display && retried.overviewOCR.funding_rate_display) overviewOCR.funding_rate_display = retried.overviewOCR.funding_rate_display;
    if (!overviewOCR.open_interest && retried.overviewOCR.open_interest) overviewOCR.open_interest = retried.overviewOCR.open_interest;
    if (!overviewOCR.long_short_24h && retried.overviewOCR.long_short_24h) overviewOCR.long_short_24h = retried.overviewOCR.long_short_24h;
    ocr = retried.ocr;
  }
  const ocrExtracted = {
    funding_rate_display: overviewOCR.funding_rate_display,
    open_interest: overviewOCR.open_interest,
    long_short_24h: overviewOCR.long_short_24h,
    cvd_candles: pickValue(ocr, { yMin: 0.60, yMax: 0.67, yTarget: 0.638, pattern: /^-?[\d.]+[KM]$/ }),
    aggregated_spot_cvd: pickValue(ocr, { yMin: 0.46, yMax: 0.52, yTarget: 0.489, pattern: /^-?[\d.]+[KM]$/ }),
    funding_weighted_panel: pickValue(ocr, { yMin: 0.33, yMax: 0.39, yTarget: 0.346, pattern: /^-?[\d.]+$/ }),
    oi_candles: pickValue(ocr, { yMin: 0.20, yMax: 0.26, yTarget: 0.226, pattern: /^-?[\d.]+[KM]$/ }),
    aggregated_futures_bid_ask_delta: validateBidAskDelta(
      pickNumericNearLabel(ocr, {
        labelPattern: /Aggregated Futures Bid/i,
        yTolerance: 0.05,
        xMin: 0.55,
        valuePattern: /^-?[\d.]+[KM]?$/,
      }) || pickValue(ocr, { yMin: 0.07, yMax: 0.13, yTarget: 0.096, pattern: /^-?[\d.]+[KM]?$/, xMin: 0.70 })
    ),
  };

  const iframeStudies = iframeText ? {
    'Cumulative Volume Delta (CVD Candles)': extractStudyValueBlock(iframeText, 'Cumulative Volume Delta (CVD Candles)', /^-?[\d.]+[KM]$/i),
    'Aggregated Spot Cumulative Volume Delta (CVD Candles)': extractStudyValueBlock(iframeText, 'Aggregated Spot Cumulative Volume Delta (CVD Candles)', /^-?[\d.]+[KM]$/i),
    'Funding Rates(Open Interest Weighted)': extractStudyValueBlock(iframeText, 'Funding Rates(Open Interest Weighted)', /^-?[\d.]+$/i),
    'Open Interest (Candles)': extractStudyValueBlock(iframeText, 'Open Interest (Candles)', /^-?[\d.]+[KM]$/i),
    'Aggregated Futures Bid & Ask Delta': extractStudyValueBlock(iframeText, 'Aggregated Futures Bid & Ask Delta', /^-?[\d.]+[KM]?$/i),
  } : null;

  const domExtracted = {
    cvd_candles: iframeStudies?.['Cumulative Volume Delta (CVD Candles)']?.at(-1) || null,
    aggregated_spot_cvd: iframeStudies?.['Aggregated Spot Cumulative Volume Delta (CVD Candles)']?.at(-1) || null,
    funding_weighted_panel: iframeStudies?.['Funding Rates(Open Interest Weighted)']?.[0] || null,
    oi_candles: iframeStudies?.['Open Interest (Candles)']?.at(-1) || null,
    aggregated_futures_bid_ask_delta: validateBidAskDelta(iframeStudies?.['Aggregated Futures Bid & Ask Delta']?.[0] || null),
  };

  const apiPrice = await fetchBtcPriceUsd();

  const extracted = {
    price: apiPrice ?? overview.price,
    exchange_funding_rate_display: overview.funding_rate_display || ocrExtracted.funding_rate_display,
    exchange_open_interest_display: overview.open_interest || ocrExtracted.open_interest,
    exchange_long_short_24h_display: overview.long_short_24h || ocrExtracted.long_short_24h,
    funding_rate: domExtracted.funding_weighted_panel || ocrExtracted.funding_weighted_panel,
    open_interest: domExtracted.oi_candles || ocrExtracted.oi_candles,
    long_short_24h: null,
    cvd_candles: domExtracted.cvd_candles || ocrExtracted.cvd_candles,
    aggregated_spot_cvd: domExtracted.aggregated_spot_cvd || ocrExtracted.aggregated_spot_cvd,
    funding_weighted_panel: domExtracted.funding_weighted_panel || ocrExtracted.funding_weighted_panel,
    oi_candles: domExtracted.oi_candles || ocrExtracted.oi_candles,
    aggregated_futures_bid_ask_delta: domExtracted.aggregated_futures_bid_ask_delta || ocrExtracted.aggregated_futures_bid_ask_delta,
  };

  const scanKey = `${t.date}T${t.hm.slice(0,2)}:${t.hm.slice(2)}`;
  const result = {
    scan_key: scanKey,
    source: 'coinglass_browser_cdp_dom_ocr',
    symbol: 'BTCUSDT',
    exchange: 'Binance',
    timeframe: '1H',
    ...extracted,
    conclusion: '观望',
    paper_trade_action: 'NONE',
    screenshot_path: screenshotPath,
    overview_crop_path: fs.existsSync(overviewCropPath) ? overviewCropPath : null,
    archive_dir: runDir,
    page_url: PAGE_URL,
    captured_at: t.iso,
    extraction_debug: {
      dom: domExtracted,
      ocr: ocrExtracted,
      iframe_studies: iframeStudies,
    },
    status: Object.values(extracted).every(v => v !== null) ? 'ok' : 'partial',
    note: 'Framework fields prefer aggregated sources. funding_rate uses Funding Rates(Open Interest Weighted); open_interest uses panel OI candles. Right-side Binance display fields are stored separately for reference only.'
  };

  fs.writeFileSync(path.join(runDir, 'ocr.json'), JSON.stringify(ocr, null, 2));
  fs.writeFileSync(path.join(runDir, 'dom.json'), JSON.stringify({ iframeStudies, liveDisplay: domSnapshot?.display || {} }, null, 2));
  fs.writeFileSync(path.join(runDir, 'meta.json'), JSON.stringify({ page_url: PAGE_URL, captured_at: t.iso, cdp_port: DEBUG_PORT, cdp_auto_started: cdp.started, chrome_bin: cdp.chromeBin || null, response_urls: responses.map(r => r.url).filter((v, i, a) => a.indexOf(v) === i) }, null, 2));
  fs.writeFileSync(path.join(runDir, 'scan.json'), JSON.stringify(result, null, 2));
  fs.appendFileSync(path.join(ARCHIVE, 'scans.ndjson'), JSON.stringify(result) + '\n');
  fs.writeFileSync(path.join(runDir, 'scan.md'), [
    `scan_key: ${result.scan_key}`,
    `price: ${result.price}`,
    `funding_rate: ${result.funding_rate}`,
    `open_interest: ${result.open_interest}`,
    `long_short_24h: ${result.long_short_24h}`,
    `exchange_funding_rate_display: ${result.exchange_funding_rate_display}`,
    `exchange_open_interest_display: ${result.exchange_open_interest_display}`,
    `exchange_long_short_24h_display: ${result.exchange_long_short_24h_display}`,
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
