from bist_signal_bot.data_import.normalization import ImportNormalizer
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine
from bist_signal_bot.data_import.models import ImportDatasetType
from bist_signal_bot.config.settings import Settings
import pandas as pd

normalizer = ImportNormalizer(Settings())
engine = SchemaMappingEngine(Settings())

df = pd.DataFrame({
    "symbol": ["thyao ", "THYAO "],
    "date": ["2024-01-01", "2024-01-01"], # duplicate
    "close": ["1.234,56", "1.234,56"]
})
mapping = engine.infer_mapping(["symbol", "date", "close"], ImportDatasetType.OHLCV)

df_norm, stats = normalizer.normalize_dataframe(df, mapping, ImportDatasetType.OHLCV)
print("DF Length:", len(df_norm))
print(df_norm)
