# Data Spec

## 目标

这份文档定义后续学习、记录和 1 年回测准备时的最小数据口径。
当前先定研究草案，不代表最终版。

## 推荐主周期
- 执行周期：`1h`
- 背景周期：`4h`

原因：
- 比 5m/15m 更少噪音
- 比日线更适合 V1/V2 当前叙事
- 适合先做 1 年事件研究

## 核心字段

### 1. Price OHLCV
必需：
- timestamp
- open
- high
- low
- close
- volume

用途：
- 定义价格方向
- 判断 higher high / lower low
- 计算信号后收益

### 2. Funding Rate
必需：
- timestamp
- funding_rate_raw
- source
- aggregation_type

当前优先级：
1. 全网 OI 加权 funding
2. 多交易所加权 funding
3. 单交易所 funding

要求：
- 明确是否为 8h 原值
- 不混用 annualized 和 raw

### 3. Open Interest
必需：
- timestamp
- oi_value
- oi_change_1h
- source

用途：
- 区分新开仓 vs 去杠杆
- 配合价格判断 squeeze / 趋势

### 4. Spot CVD
必需：
- timestamp
- spot_cvd_value
- spot_cvd_change_1h
- source

要求：
- 必须写清聚合范围
- 必须固定周期

### 5. Futures CVD
必需：
- timestamp
- futures_cvd_value
- futures_cvd_change_1h
- source

### 6. Orderbook / Liquidation Context
当前允许先用弱化字段：
- orderbook_bias: `-1 / 0 / +1`
- liquidation_bias: `-1 / 0 / +1`

说明：
- 这一块最难标准化
- 学习阶段先记录方向，不强求高精度数值

## 信号记录表

建议后续统一成一张 signal log，至少包含：
- timestamp
- framework_mode: `V1 | V2 | WATCH`
- direction: `LONG | SHORT | NONE`
- fr
- oi_change_1h
- spot_cvd_change_1h
- futures_cvd_change_1h
- orderbook_bias
- liquidation_bias
- signal_strength: `candidate | strong`
- note

## 数据质量分级
- A: 全网聚合 / 结构化数据
- B: 多交易所加权估算
- C: 单交易所替代
- D: 截图人工读数

回测时建议：
- A/B 可用于研究
- C 仅用于弱化验证
- D 不作为主回测依据

## 当前结论

如果要做 1 年回测，最低要求是先把：
- Price
- Funding
- OI
- Spot/Futures CVD

这 4 类字段口径固定下来。
Orderbook 和 liquidation 可以后补。 
