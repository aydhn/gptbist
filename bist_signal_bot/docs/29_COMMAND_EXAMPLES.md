# Command Examples
python -m bist_signal_bot breadth snapshot --symbols ASELS THYAO GARAN

# Research Lab
python -m bist_signal_bot lab plan daily --symbols ASELS THYAO GARAN
python -m bist_signal_bot lab enqueue --job BACKTEST --symbol ASELS --strategy moving_average_trend
python -m bist_signal_bot lab run --next
