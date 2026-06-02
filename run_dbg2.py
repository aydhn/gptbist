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

df_norm = engine.apply_mapping(df.copy(), mapping)
print("Mapped:", df_norm)

for col_mapping in mapping.column_mappings:
    target_col = col_mapping.target_column
    if target_col not in df_norm.columns:
        continue
    sem_type = col_mapping.semantic_type

    if sem_type == "SYMBOL":
        df_norm[target_col] = df_norm[target_col].apply(normalizer.normalize_symbol)
    elif sem_type in ("DATE", "DATETIME"):
        df_norm[target_col] = df_norm[target_col].apply(normalizer.normalize_date)
    elif sem_type in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
         print(f"Col {target_col} Type before numeric:", df_norm[target_col].dtype)
         if df_norm[target_col].dtype == object:
             df_norm[target_col] = df_norm[target_col].apply(normalizer.normalize_numeric)
         print(f"Col {target_col} Values before to_numeric:\n", df_norm[target_col])
         df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')
         print(f"Col {target_col} Values after to_numeric:\n", df_norm[target_col])

print("\nBefore drop:", df_norm)
req_cols = [m.target_column for m in mapping.column_mappings if m.required and m.target_column in df_norm.columns]
print("Req cols:", req_cols)
df_valid, removed = normalizer.drop_invalid_required(df_norm, req_cols)
print("\nAfter drop:", df_valid)
