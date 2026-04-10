# Backtest Rules V1

## 目标

这是 V1 的首版回测规则草案。
目的不是最优，而是先做到：
- 明确
- 可执行
- 可复盘

## 周期
- 主周期：`1h`
- 背景周期：`4h`

## 方向
V1 是逆向极值框架。
- 极端负 funding，优先找 LONG
- 极端正 funding，优先找 SHORT

## LONG 触发条件
同一根 1h bar 收盘时检查：

1. `funding_rate <= -0.0040`
2. `futures_cvd_change_1h < 0`
3. `spot_cvd_change_1h >= 0` 或 `spot_cvd_change_1h` 的恶化程度明显小于 `futures_cvd_change_1h`
4. `oi_change_1h <= 0`

首版简化触发：
- 满足 4 条中的至少 3 条，触发 V1 LONG candidate
- 其中条件 1 必须满足

## SHORT 触发条件
同一根 1h bar 收盘时检查：

1. `funding_rate >= +0.0040`
2. `futures_cvd_change_1h > 0`
3. `spot_cvd_change_1h <= 0` 或其改善程度明显弱于 `futures_cvd_change_1h`
4. `oi_change_1h <= 0`

首版简化触发：
- 满足 4 条中的至少 3 条，触发 V1 SHORT candidate
- 其中条件 1 必须满足

## 入场规则
首版先用最简单版本：
- 信号出现后的下一根 1h bar open 入场

说明：
- 暂不等待清算密集区回踩
- 这样更适合第一版验证
- 回踩入场可在第二版加入

## 出场规则
首版先固定三种退出方式，谁先到用谁：

### LONG
- 止损：`entry - 1.5 * ATR(14, 1h)`
- 止盈：`entry + 3.0 * ATR(14, 1h)`
- 超时退出：持有满 24 根 1h bar

### SHORT
- 止损：`entry + 1.5 * ATR(14, 1h)`
- 止盈：`entry - 3.0 * ATR(14, 1h)`
- 超时退出：持有满 24 根 1h bar

## 过滤条件
以下情况首版建议跳过：
- funding 数据缺失
- spot / futures CVD 任一缺失
- OI 缺失
- 宏观事件窗口（后续补事件表）

## 记录字段
每次触发至少记录：
- timestamp
- direction
- funding_rate
- futures_cvd_change_1h
- spot_cvd_change_1h
- oi_change_1h
- conditions_met_count
- entry_price
- exit_price
- exit_reason
- pnl

## 当前限制
这不是最终版本。
它只是第一版可跑规则，用于回答：

**V1 在过去 1 年里，是否至少存在可观察的方向优势。**
