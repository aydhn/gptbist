import os
from pathlib import Path

# Fix numeric parsing
norm_path = Path("bist_signal_bot/data_import/normalization.py")
content = norm_path.read_text()
# df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric) was applied but then pd.to_numeric runs again.
# Wait, if we use pd.to_numeric with coerce, it will turn float objects back into float, which is fine, but maybe apply didn't run?
content = content.replace("df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)", "df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)")
norm_path.write_text(content)

# Ah wait, `normalize_numeric` is converting to float, then `pd.to_numeric` works.
# But wait, look at test:
# def test_normalize_numeric_comma():
#    normalizer = ImportNormalizer(Settings())
#    assert normalizer.normalize_numeric("1.234,56") == 1234.56
# So normalize_numeric works. Then why is it dropped?
# Let's check what `drop_invalid_required` does.
# df_valid = df.dropna(subset=existing_req)
# If existing_req has "symbol", "date", "close", are any of them NaN?
# symbol is "thyao " -> "THYAO". date is "2024-01-01" -> "2024-01-01". close is "1.234,56" -> 1234.56.
# Why would it be dropped?
# Let's print out the df inside the test.
