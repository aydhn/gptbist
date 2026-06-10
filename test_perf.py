import time
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.config.settings import Settings

settings = Settings()
provider = MockMarketDataProvider()
service = MarketDataService(settings=settings, provider=provider)

symbols = [f"SYM{i}" for i in range(100)]

start = time.time()
res1 = {}
for sym in symbols:
    mdf = service.get_ohlcv(sym, "1d")
    if mdf and not mdf.data.empty:
        res1[sym] = mdf
t1 = time.time() - start

start = time.time()
res2 = service.get_many_ohlcv(symbols, "1d")
t2 = time.time() - start

print(f"N+1 loop time: {t1:.4f}s")
print(f"get_many_ohlcv time: {t2:.4f}s")
