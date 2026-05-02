python -m bist_signal_bot patterns list
python -m bist_signal_bot patterns list --category BREAKOUT
python -m bist_signal_bot patterns detect ASELS --source mock --pattern price_breakout:window=20
python -m bist_signal_bot patterns detect ASELS --source mock --pattern rolling_sr:window=50
python -m bist_signal_bot patterns detect ASELS --source mock --default-set
python -m bist_signal_bot pattern-features ASELS --source mock --level basic
python -m bist_signal_bot pattern-features ASELS --source mock --level advanced
python -m bist_signal_bot pattern-features ASELS --source mock --level full
python -m bist_signal_bot pattern-features ASELS --source mock --level full --json
python -m bist_signal_bot healthcheck
