
# SYNTHETIC SCENARIO WORKFLOW

```bash
python -m bist_signal_bot synthetic-scenarios list
python -m bist_signal_bot synthetic-scenarios show trend_up_basic_v1
python -m bist_signal_bot synthetic-scenarios generate --scenario trend_up_basic_v1 --dry-run
python -m bist_signal_bot synthetic-scenarios export --scenario trend_up_basic_v1 --format csv --confirm
```
