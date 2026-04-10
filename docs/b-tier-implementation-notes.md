# B-Tier Implementation Notes

## 首版实现目标

先拉到这些字段：
- price
- funding
- oi
- 简化 flow proxy

## flow proxy 候选

如果暂时拿不到高质量 CVD，可先试：
- taker buy volume / taker sell volume
- taker buy ratio
- 现货与合约价格动量差

说明：
这些不是原版 spot/futures CVD。
但可以先作为弱代理做 first-pass 研究。

## 首版研究输出

至少先输出两类结果：

1. 事件研究
- V1 后 1h / 4h / 24h 收益
- V2 后 4h / 24h / 48h 收益

2. 触发统计
- 触发次数
- 多空占比
- 平均后续收益
- 不同市场环境下的结果

## 当前边界

B 档阶段先别追求：
- 完美复刻 CoinGlass 页面
- 高精度 liquidation map
- 过于复杂的评分系统

先证明值得继续，再加复杂度。 
