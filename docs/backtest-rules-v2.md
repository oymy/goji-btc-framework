# Backtest Rules V2

## 目标

这是 V2 的首版回测规则草案。
V2 不是抓极值反转，而是抓中性 funding 环境下的趋势共振。

## 周期
- 主周期：`1h`
- 背景周期：`4h`

## 前置条件
同一根 1h bar 收盘时检查：

1. `abs(funding_rate) <= 0.0010`
2. 不存在明显 spot / futures 冲突

首版里，“明显冲突”简化为：
- futures_cvd_change_1h > 0 且 spot_cvd_change_1h < 0
- 或 futures_cvd_change_1h < 0 且 spot_cvd_change_1h > 0

出现冲突则不触发 V2。

## LONG 打分
- `spot_cvd_change_1h > 0` → `+3`
- `oi_change_1h > 0` 且 `close_change_1h > 0` → `+1`
- `orderbook_bias = +1` → `+1`
- `liquidation_bias = +1` → `+1`

首版阈值：
- 总分 `>= +5` 触发 V2 LONG

## SHORT 打分
- `spot_cvd_change_1h < 0` → `-3`
- `oi_change_1h > 0` 且 `close_change_1h < 0` → `-1`
- `orderbook_bias = -1` → `-1`
- `liquidation_bias = -1` → `-1`

首版阈值：
- 总分 `<= -5` 触发 V2 SHORT

## 入场规则
- 信号出现后的下一根 1h bar open 入场

## 出场规则
### LONG
- 止损：`entry - 1.5 * ATR(14, 1h)`
- 止盈：`entry + 3.0 * ATR(14, 1h)`
- 超时退出：持有满 48 根 1h bar

### SHORT
- 止损：`entry + 1.5 * ATR(14, 1h)`
- 止盈：`entry - 3.0 * ATR(14, 1h)`
- 超时退出：持有满 48 根 1h bar

## 弱化版说明
如果首版缺少 orderbook / liquidation 的高质量数据，可先做弱化验证：
- 只使用 Spot CVD + OI + Funding regime
- 把阈值从 `5` 下调到 `4`
- 但必须在结果中明确标注是弱化版

## 记录字段
每次触发至少记录：
- timestamp
- direction
- funding_rate
- spot_cvd_change_1h
- oi_change_1h
- close_change_1h
- orderbook_bias
- liquidation_bias
- score
- entry_price
- exit_price
- exit_reason
- pnl

## 当前限制
V2 的问题比 V1 更大：
- 更依赖多字段同时稳定
- 更容易受数据质量影响
- 更可能因为评分设计不同而结果变化很大

所以 V2 回测结果必须比 V1 更谨慎地解读。
