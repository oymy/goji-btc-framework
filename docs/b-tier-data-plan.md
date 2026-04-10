# B-Tier Data Plan

## 目标

用免费或低成本公开数据，先完成 first-pass 研究。

## B 档大概损失了什么

### 保留得比较好的
- Price OHLCV
- 单所 funding
- 单所 OI
- 多所加权 funding / OI

这部分通常能保留原框架研究价值的 70% 到 85%。

### 损失比较大的
- 全网聚合 spot CVD
- 全网聚合 futures CVD
- liquidation heatmap 细节
- orderbook / liquidation 的统一口径

这部分通常只能保留 40% 到 60%。

## 为什么仍然值得先用 B 档

因为当前最重要的问题不是“完美复刻原框架”，而是：

**这套思路在弱化条件下，是否仍然有方向偏移。**

如果弱化后完全没东西，再上 A 档意义也不大。

## B 档首版建议数据

### 必要
- Binance BTCUSDT perp OHLCV
- Binance funding
- Binance OI
- Bybit funding
- Bybit OI
- OKX funding
- OKX OI

### 可选
- 现货 OHLCV（Binance / Coinbase）
- taker buy/sell volume 作为弱代理

## B 档首版简化

### V1
保留：
- funding 极值
- OI 变化
- price move
- 弱化版 flow proxy

### V2
保留：
- funding 中性
- OI + price 共振
- 弱化版 flow proxy

### 暂时弱化处理
- liquidation heatmap
- orderbook imbalance
- 高质量聚合 CVD

## 当前建议

先别纠结 B 档和 A 档差的那 20% 到 40%。
先把 B 档跑起来，看有没有基本偏移。

如果有，再决定是否升级。 
