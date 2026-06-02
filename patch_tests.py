import os
from pathlib import Path

# PathGuard is mocking out a check in our stub, let's fix the test or the stub.
pg_path = Path("bist_signal_bot/security/path_guard.py")
if pg_path.exists():
    content = pg_path.read_text()
    if "is_absolute" not in content:
        new_pg = """
from pathlib import Path
class PathGuard:
    @staticmethod
    def ensure_safe_path(path: Path, base_dir: Path | None = None) -> None:
        p_str = str(path)
        if ".." in p_str:
            raise ValueError("Path traversal attempt")
        if base_dir:
            try:
                # if path is absolute but not inside base_dir, this raises ValueError
                path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                raise ValueError("Path outside base_dir")
        elif path.is_absolute():
             # if no base_dir provided, reject absolute paths as potentially unsafe in tests
             # unless we know it's fine. For test_check_unsafe_path it expects /etc/passwd to fail.
             raise ValueError("Absolute paths not allowed without base_dir")
"""
        pg_path.write_text(new_top + new_pg if 'new_top' in locals() else new_pg)

# Fix test_normalize_dataframe
# It was failing because missing required targets caused `df_valid.dropna(subset=existing_req)` to drop everything if there are nulls. Wait, let's look at the mapping logic.
# SchemaMappingEngine for OHLCV requires `open, high, low, volume`.
# We only provided symbol, date, close.
# So open, high, low, volume are missing required.
# In `ImportNormalizer.drop_invalid_required`, we check `m.required`.
# Since open, high, low, volume are required but missing from `df_norm.columns`, `existing_req` will only be `symbol, date, close`.
# Why did it drop everything? Because we are not providing values that are null.
# Ah, `existing_req` contains the target columns that exist.
# Let's check `pd.to_numeric(df_norm["close"])` - "1.234,56" became NaN if decimal comma is not properly handled?
# "1.234,56" parsing:
