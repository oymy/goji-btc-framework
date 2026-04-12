# Archive Structure

## 目标

每次扫描都保留可人工复核的证据。

## 建议目录

`data/runs/YYYY-MM-DD/HHmm/`

每次扫描保存：
- `screenshot.png` 页面截图
- `scan.json` 提取出的关键字段
- `scan.md` 人类可读摘要
- `meta.json` 扫描时间、页面、周期、说明

## scan.json 建议字段
- symbol
- timeframe
- price
- funding_rate
- open_interest
- long_short_24h
- conclusion
- status
- source = coinglass_screenshot

## 组织原则
- 一次扫描一个目录
- 日期分目录
- 时间精确到分钟
- 所有结果都可回溯到截图
