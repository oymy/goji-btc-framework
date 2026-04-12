# Publish Flow

## 输出目标

每次扫描后同时发到：
- Discord 当前频道
- 微信

## 单次扫描产物
1. 本地留档
2. 人类可读摘要
3. 截图
4. 发送摘要 + 截图

## 摘要格式
- 时间
- 标的
- Price
- Funding Rate
- Open Interest
- Long/Short 24h
- 结论
- 备注：截图版，接近原版但非完整自动五指标版

## 当前现实
真正自动发消息前，还需要把：
- 截图获取
- 文本提取
- message 发送
串起来。
