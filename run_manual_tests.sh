mkdir -p data/imports
echo "symbol,date,open,high,low,close,volume" > data/imports/ohlcv.csv
echo "THYAO,2024-01-01,100,105,99,104,1000" >> data/imports/ohlcv.csv

echo '{"symbol": "THYAO", "period": "2024Q1", "revenue": 1000}' > data/imports/financials.jsonl
echo '{"symbol": "GARAN", "period": "2024Q1", "revenue": 2000}' >> data/imports/financials.jsonl

echo "date,indicator,value" > data/imports/macro.csv
echo "2024-01-01,CPI,65.0" >> data/imports/macro.csv

python -m bist_signal_bot data-import formats
python -m bist_signal_bot data-import preview --path data/imports/ohlcv.csv --type OHLCV
python -m bist_signal_bot data-import map --path data/imports/ohlcv.csv --type OHLCV
python -m bist_signal_bot data-import validate --path data/imports/financials.jsonl --type FINANCIALS --json
python -m bist_signal_bot data-import normalize --path data/imports/ohlcv.csv --type OHLCV --dry-run
python -m bist_signal_bot data-import run --path data/imports/ohlcv.csv --type OHLCV --confirm
python -m bist_signal_bot data-import jobs
python -m bist_signal_bot data-import report
