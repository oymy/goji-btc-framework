# Signal Log Template

建议后续把每次信号统一记录成表。

## 字段
- timestamp
- framework_mode
- direction
- funding_rate
- futures_cvd_change_1h
- spot_cvd_change_1h
- oi_change_1h
- close_change_1h
- orderbook_bias
- liquidation_bias
- conditions_met_count
- score
- signal_strength
- data_quality
- entry_price
- exit_price
- exit_reason
- pnl
- note

## CSV 示例

```csv
timestamp,framework_mode,direction,funding_rate,futures_cvd_change_1h,spot_cvd_change_1h,oi_change_1h,close_change_1h,orderbook_bias,liquidation_bias,conditions_met_count,score,signal_strength,data_quality,entry_price,exit_price,exit_reason,pnl,note
2026-04-02 09:00:00,V1,LONG,-0.0061,-180,-15,-0.8,-1.2,0,1,4,,strong,B,65320,66780,tp,1460,"tariff shock day; candidate squeeze"
```

## 用途
- 做人工复盘
- 做事件研究
- 做回测结果抽样检查
- 比对失败案例
