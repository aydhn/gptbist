# Monitoring Workflow Examples
```bash
python -m bist_signal_bot monitoring status
python -m bist_signal_bot monitoring run --object-type STRATEGY --object-id moving_average_trend
python -m bist_signal_bot monitoring decay --object-type STRATEGY --object-id moving_average_trend
python -m bist_signal_bot monitoring champion-challenger --object-type STRATEGY --champion moving_average_trend --challenger breakout_trend
python -m bist_signal_bot monitoring alerts
python -m bist_signal_bot monitoring watchlist
python -m bist_signal_bot monitoring report
```
