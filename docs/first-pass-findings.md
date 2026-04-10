# First-Pass Findings

## 当前环境

- Binance API: 451
- Bybit API: 403
- OKX API: 可用（通过 Clash 代理）

当前研究仍是：

**OKX 单所弱化版 first-pass。**

## 1. 原始固定阈值无效

按原文档 V1 阈值：
- `funding_rate <= -0.0040`
- `funding_rate >= +0.0040`

在当前 OKX 单所样本里：
- `min = -0.000071`
- `max = 0.000100`

结果：
- **0 次触发**

结论：
- 原阈值不能直接迁移到单所口径

## 2. percentile 版 funding 单因子有点东西

### p90 / p10
- LONG: `10`
- SHORT: `9`
- LONG 24h 平均：`+1.26%`
- SHORT 24h 按做空方向：`+0.75%`
- 4h 效果弱

### p95 / p05
- 信号更少
- 效果没更好

### p99 / p01
- 样本太少

当前拍板：
- **p90 / p10** 是当前最合理的 first-pass funding 阈值

## 3. funding + OI 双因子暂时没更好

我又加了：
- funding 处于极端 percentile
- OI 1h change <= 0

结果：
- LONG: `0`
- SHORT: `10`
- SHORT 4h 按做空方向：`+0.19%`
- SHORT 24h 按做空方向：`-0.60%`

结论：
- 当前样本里，简单把 “OI 下降” 叠到 funding 极值上，**没有增强 V1**
- 至少在这个弱化版里，它还不是一个好过滤器

## 当前最重要的结论

1. 原框架的固定 funding 阈值不稳
2. percentile funding 更合理
3. 当前样本里，V1 更像 **24h 级别均值回归**
4. funding + OI 这个双因子版本，暂时没跑出更强结果

## 暂时判断

如果只看目前能拿到的数据：

- **funding 极值思路值得继续研究**
- **固定 0.0040 阈值不值得保留**
- **OI 在当前弱化实现里还没证明自己能提高信号质量**
