import os
from pathlib import Path

# Fix the sem_type.value check
norm_path = Path("bist_signal_bot/data_import/normalization.py")
content = norm_path.read_text()
# Previously `sem_type.value in ...`
# Let's fix that section
old = """            elif sem_type.value in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
                 # Handle decimal comma if enabled
                 if getattr(self.settings, "DATA_IMPORT_NORMALIZE_DECIMAL_COMMA", True):
                     if df_norm[target_col].dtype == object or str(df_norm[target_col].dtype) == "string":
                         df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)

                 # Ensure numeric type
                 df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')"""

new = """            elif sem_type.value in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
                 # Handle decimal comma if enabled
                 if getattr(self.settings, "DATA_IMPORT_NORMALIZE_DECIMAL_COMMA", True):
                     # apply directly, self.normalize_numeric handles strings/floats well.
                     df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)

                 # Ensure numeric type
                 df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')"""

content = content.replace(old, new)
norm_path.write_text(content)
