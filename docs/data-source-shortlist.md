# Data Source Shortlist

## Tier 1

### OKX 官方历史数据 / API
用途：
- funding
- candles

判断：
- **最靠谱**
- 当前环境已验证可用

### supervik/historical-funding-rates-fetcher
用途：
- 多交易所 funding CSV
- funding percentile / regime 研究

判断：
- **最适合当前阶段补 funding 研究**
- 但不能单独完成 V1/V2 回测

## Tier 2

### jesusgraterol/binance-futures-dataset-builder
用途：
- funding / OI / taker buy-sell 方向上的数据生成思路

判断：
- 更像生成器，不是现成完整数据仓

### aoki-h-jp/funding-rate-arbitrage
用途：
- 多所 funding 监控与策略研究

判断：
- 更偏工具，不是现成历史数据

## Tier 3

### sferez/BybitMarketData
用途：
- Bybit 原始 market event

判断：
- 太重
- 适合深度研究，不适合当前快速推进

## 当前拍板

优先级：
1. OKX 官方
2. supervik funding CSV
3. 其他暂不优先
