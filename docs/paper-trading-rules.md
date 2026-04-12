# Paper Trading Rules

## 账户
- 初始资金：1000U
- 单笔仓位：20%
- 多空都做
- 只有明确做多/做空才开仓
- 观望不开仓

## 去重规则
- 只认 Discord cron 的扫描结果
- 微信只收通知，不参与记账
- 同一时间点只允许记一笔扫描结果

## 账本文件
- `data/paper_account.json`
- `data/paper_trades.csv`

## 当前状态
模拟盘规则已落文件，但自动记账逻辑还没接进 `/trading-scan` 执行链。
