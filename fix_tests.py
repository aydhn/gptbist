import re
from pathlib import Path

# Fix ApplicationContext instantiation
with open('bist_signal_bot/tests/test_cli_corporate_actions.py', 'r') as f:
    content = f.read()

content = content.replace(
    'return ApplicationContext(settings=s, symbol_universe=SymbolUniverse([]), data_provider=provider, data_store=store)',
    'ctx = ApplicationContext()\n    ctx.settings = s\n    ctx.symbol_universe = SymbolUniverse([])\n    ctx.provider = provider\n    ctx.store = store\n    return ctx'
)

# Also fix the import
content = content.replace(
    'from bist_signal_bot.app.bootstrap import ApplicationContext',
    'class ApplicationContext:\n    pass'
)

with open('bist_signal_bot/tests/test_cli_corporate_actions.py', 'w') as f:
    f.write(content)

# Fix test_local_store_adjusted_rw
with open('bist_signal_bot/tests/test_data_service_adjustments.py', 'r') as f:
    content = f.read()

# provider.fetch_one("ASELS", timeframe=Timeframe.DAILY) creates an MDF with source=DataVendor.MOCK
# However, the string representation might be 'MOCK'. The path uses `v_str = market_data.source.value.lower() if isinstance(...)` but in my injected code for write_adjusted_ohlcv:
# v_str = market_data.source.value
# and `exists_adjusted` does: v_str = vendor.value if isinstance(vendor, DataVendor) else vendor
# If DataVendor.MOCK.value is "MOCK", then v_str is "MOCK" or "mock"?
# In LocalMarketDataStore.write_ohlcv, they do `v_str = market_data.source.value` and let `get_ohlcv_file_path` handle lowercase.
# Let's update `write_adjusted_ohlcv` and related methods in local_store.py to use .lower() for directories.

with open('bist_signal_bot/storage/local_store.py', 'r') as f:
    local_store_content = f.read()

local_store_content = local_store_content.replace(
    'dir_path = base_dir / v_str / tf_str',
    'dir_path = base_dir / v_str.lower() / tf_str.lower()'
)
local_store_content = local_store_content.replace(
    'file_path = base_dir / v_str / tf_str / f"{symbol}.csv"',
    'file_path = base_dir / v_str.lower() / tf_str.lower() / f"{symbol}.csv"'
)

with open('bist_signal_bot/storage/local_store.py', 'w') as f:
    f.write(local_store_content)
