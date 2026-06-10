import time
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.models import DataFetchRequest, Timeframe

symbols = [f"SYM{i}" for i in range(100)]
provider = MockMarketDataProvider()

# Current N+1 implementation simulation
start = time.time()
res_n1 = {}
for sym in symbols:
    res_n1[sym] = provider.fetch_one(sym, Timeframe.DAILY)
t_n1 = time.time() - start

# Current fetch_ohlcv implementation (which is what DataFetchRequest uses)
req = DataFetchRequest(symbols=symbols, timeframe=Timeframe.DAILY, period="2y")
start = time.time()
res_batch = provider.fetch_ohlcv(req)
t_batch = time.time() - start

print(f"N+1 time: {t_n1:.4f}s")
print(f"Batch time: {t_batch:.4f}s")
