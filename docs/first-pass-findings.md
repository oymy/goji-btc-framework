# First-Pass Findings

## 当前结果

在当前机器 + Clash 代理环境下：
- Binance API 仍返回 451
- Bybit API 仍返回 403
- OKX API 可用

因此 first-pass 研究暂时降级为：

**OKX 单所弱化版。**

## 已拿到的数据
- OKX funding history: 100 条
- OKX open interest: 1 条当前值
- OKX 1h candles: 3000 条

## 第一个重要发现

按原文档的 V1 阈值：
- `funding_rate <= -0.0040`
- `funding_rate >= +0.0040`

在当前 OKX 单所 funding 数据里：
- `min = -0.000071`
- `max = 0.000100`

结果：

**0 次触发。**

## 这说明什么

最合理的解释不是“市场 1 年里都没有 V1 机会”，而是：

**原阈值严重依赖原作者使用的特定聚合 funding 口径。**

换成单所口径后，阈值直接失真。

## 当前结论

1. 文档里写死的 funding 阈值不能直接跨数据源复用
2. 如果用 B 档单所数据，必须改成：
   - 分位数阈值
   - 或单所重新标定阈值
3. 这进一步证明原框架当前更像经验框架，而不是可直接迁移的通用规则

## 下一步建议

如果继续做单所 first-pass，建议：
- V1 改成 rolling percentile 阈值
- V2 优先于 V1 先做弱化版验证
- OI 历史数据需要继续补抓，否则 V1/V2 都不完整
