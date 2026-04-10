# Funding Threshold Research

## 数据来源

本轮接入两部分数据：
- `supervik/historical-funding-rates-fetcher` 的 BTC-USDT 多所 funding CSV
- 当前通过 OKX API 抓到的单所 funding + 1h candles

## 第一结论

### 固定阈值 `±0.0040` 不适合作为通用阈值
多所历史结果显示：
- Binance max: `0.003`
- Bybit max: `0.00375`
- Gate max: `0.00375`
- Kucoin max: `0.00375`
- MEXC max: `0.0013`
- dYdX max: `0.00059`

所以：

**`+0.0040` 在很多数据源里几乎不会出现，甚至超过历史最大值。**

## 第二结论

### 更合理的是 percentile 阈值
多所历史显示：
- p95 常见在 `0.0006 ~ 0.0008`
- p99 常见在 `0.0012 ~ 0.0020`
- 不同交易所差异明显

所以更合理的定义不是：
- 固定常数极值

而是：
- **相对该数据源自身分布的极值**

## OKX 单所 first-pass 比较

本轮测试了三档：
- p90 / p10
- p95 / p05
- p99 / p01

### p90 / p10
- LONG 数量：`10`
- SHORT 数量：`9`
- LONG 24h 平均：`+1.26%`
- SHORT 24h 按做空方向：`+0.75%`
- 4h 效果弱

### p95 / p05
- LONG 数量：`5`
- SHORT 数量：`4`
- LONG 24h 平均：`+0.89%`
- SHORT 24h 按做空方向：`+0.07%`

### p99 / p01
- LONG 数量：`1`
- SHORT 数量：`4`
- 样本太少，不足以下结论

## 当前判断

如果只看当前 OKX 单所弱化版：

1. funding 极值本身可能有研究价值
2. 24h 维度比 4h 维度更像有信息
3. **p90 / p10 比 p95 / p99 更适合 current first-pass**
4. 原仓库写死 `±0.0040` 的方式不稳

## 现在能说到哪一步

能说：
- 原框架的 funding 极值思路没有完全失效
- 但阈值定义需要重写

不能说：
- 这已经证明完整 V1 有效

因为当前还缺：
- OI 历史序列
- flow proxy
- 交易成本
- 更长样本和样本外检验

## 当前拍板

后续如果继续做弱化版 V1，优先使用：

**p90 / p10 percentile threshold**

再逐步往更完整的多因子版本推进。 
