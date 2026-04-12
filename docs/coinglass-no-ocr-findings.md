# CoinGlass BTCUSDT page: non-OCR extraction findings

Date: 2026-04-12
Page tested: `https://www.coinglass.com/tv/Binance_BTCUSDT`

## Bottom line

The currently OCR-derived panel values are available **without OCR** from the TradingView iframe DOM on the page.

The page contains a same-origin iframe:

- outer selector: `iframe#tradingview_c4f79` (the suffix is dynamic, so match `iframe[id^="tradingview_"]`)
- inside the iframe, the study legends expose the live values as plain text nodes, not just canvas pixels

This is much more reliable than screenshot OCR.

## Reliable DOM source

Inside `iframe[id^="tradingview_"]`, the visible study legend rows contain both the study title and current values.

Observed stable structure pattern for each study row:

- title node class pattern: `div.title-l31H9iuA.mainTitle-l31H9iuA...`
- values container class pattern: `div.valuesWrapper-l31H9iuA` / `div.valuesAdditionalWrapper-l31H9iuA`
- value item class pattern: `div.valueItem-l31H9iuA` / `div.valueValue-l31H9iuA`

The hash suffix may change, so do **not** hardcode full class names. Use text-anchored traversal:

1. find the iframe document
2. find the legend row whose text contains the study title
3. within that row, read the descendant value nodes

## Studies confirmed in DOM

### 1. Futures CVD candles
Study title:
- `<CoinGlass> Cumulative Volume Delta (CVD Candles)`

Observed legend values:
- four values, corresponding to OHLC-style current-candle values
- example: `38.834K 38.977K 38.834K 38.977K`

Can replace OCR field:
- `cvd_candles`

Suggested extraction:
- read all `valueItem/valueValue` texts in the legend row
- if pipeline only needs one display string, join them or use the last value depending on current logic

### 2. Aggregated spot CVD
Study title:
- `<CoinGlass> Aggregated Spot Cumulative Volume Delta (CVD Candles)`

Observed legend values:
- four OHLC-style values
- example: `9.23K 9.303K 9.23K`
  - only 3 were visible in one sample because of layout width, but the row is still text-backed

Can replace OCR field:
- `aggregated_spot_cvd`

### 3. Funding weighted panel
Study title:
- `<CoinGlass> Funding Rates(Open Interest Weighted)`

Observed legend value:
- single numeric value
- example: `−0.0004`

Can replace OCR field:
- `funding_weighted_panel`

This is the cleanest replacement.

### 4. OI candles
Study title:
- `<CoinGlass> Open Interest (Candles)`

Observed legend values:
- four OHLC-style values
- example: `95.146K 95.148K 95.057K 95.063K`

Can replace OCR field:
- `oi_candles`

### 5. Aggregated futures bid/ask delta
Study title:
- `<CoinGlass> Aggregated Futures Bid & Ask Delta`

Observed legend value:
- single numeric value
- example: `1.763K`

Can replace OCR field:
- aggregated futures bid/ask delta panel value

## Network requests observed

The page also makes direct requests to CoinGlass endpoints, visible in `performance.getEntriesByType('resource')`.

Observed endpoints:

- price candles:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance_BTCUSDT%23kline&interval=h1&...`
- futures bid/sell qty / delta related:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance_BTCUSDT%23buy_sell_qty_kline&interval=h1&...`
- funding weighted panel:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance_BTCUSDT%23avg_fr_kline&interval=h1&...`
- aggregated spot CVD related:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance,OKX,Bybit,Coinbase,Bitfinex,Kraken,Bitstamp,Crypto.com%23BTC%23aggregated_spot_buy_sell_coin&interval=h1&...`
- OI candles:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance_BTCUSDT%23coin%23oi_kline&interval=h1&...`
- aggregated futures depth / bid-ask related:
  - `https://fapi.coinglass.com/api/v2/kline?symbol=Binance,Bybit,OKX,Deribit,Bitfinex,dYdX,Bitmex,HTX,Kraken,Crypto.com,Hyperliquid,KuCoin%23BTC%231%23aggregated_contract_hundredth_depth&interval=h1&...`

Other useful page endpoints:

- overview ticker:
  - `https://fapi.coinglass.com/api/ticker?pair=BTCUSDT&exName=Binance&type=Futures`
- pair info:
  - `https://fapi.coinglass.com/api/exchange/futures/pairInfo`

## Important caveat on direct API scraping

Direct `curl` / plain HTTP requests to the above `fapi.coinglass.com` URLs returned only:

```json
{"code":"0","msg":"success","success":true}
```

So although the browser clearly uses these endpoints, reproducing them outside the live page likely needs additional request context or internal client behavior.

Conclusion:

- **DOM extraction from the TradingView iframe is confirmed and reliable now**
- **direct standalone API scraping is not yet confirmed**

## Suggested implementation strategy

Prefer this over OCR:

1. open page
2. locate `iframe[id^="tradingview_"]`
3. read `iframe.contentDocument.body.innerText` or, better, locate individual legend rows by study title
4. extract the numeric values from the matching row

Recommended anchor titles:

- `Cumulative Volume Delta (CVD Candles)`
- `Aggregated Spot Cumulative Volume Delta (CVD Candles)`
- `Funding Rates(Open Interest Weighted)`
- `Open Interest (Candles)`
- `Aggregated Futures Bid & Ask Delta`

## Practical recommendation

Yes, the current OCR fields can be replaced with DOM extraction from the iframe legend.

Strong confidence replacements:

- funding weighted panel
- OI candles
- aggregated futures bid/ask delta
- futures CVD candles
- aggregated spot CVD

I would treat the direct `fapi` endpoints as secondary research only until request replay is proven.
