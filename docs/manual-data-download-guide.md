# Manual Data Download Guide

## 当前最务实的手动数据路线

### 1. OKX 官方
优先拿：
- 历史 funding
- K 线

优点：
- 官方口径
- 当前代理下可访问

缺点：
- OI 历史支持有限
- 不能单独解决完整 V1/V2

### 2. GitHub 现成 funding 数据
当前筛下来最有用的是：
- `supervik/historical-funding-rates-fetcher`

它的价值：
- 已带 BTC 多交易所 funding CSV
- 可直接拿来做 funding 分布、percentile、regime 研究

它的不足：
- 没有 OI
- 没有 CVD
- 没有 liquidation

所以适合做：
- funding 阈值研究
- funding 单因子 first-pass

不适合做：
- 完整 V1/V2 回测

## 不建议优先走的路

### 1. 到处捡别人上传的大 CSV
问题：
- 口径经常不清楚
- 缺字段
- 时间断档
- 更新不稳定

### 2. 一开始就追全量高精度数据
问题：
- 成本高
- 工程量大
- 现在还没证明值不值得

## 当前建议

最稳路线是：
1. 用 OKX 官方数据继续跑单所弱化版
2. 用 `supervik` 的 BTC funding CSV 做多所 funding 分布研究
3. 后面再补 OI / flow proxy

## 结论

如果你要手动下载，
**优先 OKX 官方 + supervik funding CSV。**
这两条现在最容易落地。 
