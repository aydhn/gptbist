import os
from pathlib import Path

# Wait, `apply(self.normalize_numeric)` is NOT running or it is running but something is wrong.
# Let's see: `sem_type` is a string Enum. In python, `sem_type` might be evaluated as a string or Enum.
# In `SchemaMappingEngine.suggest_target`, it returns `ColumnSemanticType.SYMBOL`, etc.
# In `ImportNormalizer`: `sem_type = col_mapping.semantic_type`
# Let's change the condition to:
# `elif sem_type in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME") or getattr(sem_type, 'value', sem_type) in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):`

norm_path = Path("bist_signal_bot/data_import/normalization.py")
content = norm_path.read_text()

old = """            elif sem_type.value in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
                 # Handle decimal comma if enabled
                 if getattr(self.settings, "DATA_IMPORT_NORMALIZE_DECIMAL_COMMA", True):
                     # apply directly, self.normalize_numeric handles strings/floats well.
                     df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)

                 # Ensure numeric type
                 df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')"""

new = """            elif sem_type in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME") or getattr(sem_type, "value", sem_type) in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
                 if getattr(self.settings, "DATA_IMPORT_NORMALIZE_DECIMAL_COMMA", True):
                     df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)
                 df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')"""

content = content.replace(old, new)
norm_path.write_text(content)
