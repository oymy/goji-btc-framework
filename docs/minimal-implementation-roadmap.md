# Minimal Implementation Roadmap

## 目标

尽快把项目推进到“可以开始 first-pass 研究”。

## 最小路线

### Phase 1: 文档完成
当前已基本完成：
- 学习版规则
- 回测版规则草案
- data spec
- signal log template

### Phase 2: 数据方案定稿
先定：
- 主周期 1h
- 背景周期 4h
- 数据源先用 B 档

### Phase 3: 做弱化版数据落地
先拿：
- BTC price OHLCV
- funding
- OI
- 简化版 direction proxy

### Phase 4: 做事件研究
先不急着做完整策略收益。
先看：
- V1 信号后 1h / 4h / 24h
- V2 信号后 4h / 24h / 48h

### Phase 5: 决定是否升级数据
如果结果完全没偏移，就先别买更贵数据。
如果结果有偏移，再考虑 A 档。

## 当前最重要的一句话

先把弱化版跑通，比一开始追求完美数据更重要。 
