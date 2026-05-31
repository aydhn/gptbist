# Monitoring Workflow Example

```bash
# Check status
python -m bist_signal_bot monitoring status

# Run monitoring for a strategy
python -m bist_signal_bot monitoring run --object-type STRATEGY --object-id moving_average_trend

# Check decay
python -m bist_signal_bot monitoring decay --object-type MODEL --object-id my_model_v1

# Compare champion/challenger
python -m bist_signal_bot monitoring champion-challenger --object-type STRATEGY --champion sma_50 --challenger ema_50

# List alerts
python -m bist_signal_bot monitoring alerts

# View report
python -m bist_signal_bot monitoring report
```
