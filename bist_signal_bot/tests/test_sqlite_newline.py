import pytest
import sqlite3
from pathlib import Path
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.data_import.models import ImportSourceFormat

def test_sqlite_injection_newline(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create a table with a malicious name ending in newline to bypass `$`
    malicious_table_name = 'users\n" DROP TABLE users; --'

    safe_creation_name = malicious_table_name.replace('"', '""')
    c.execute(f'CREATE TABLE "{safe_creation_name}" (id INTEGER, name TEXT)')
    c.execute(f'INSERT INTO "{safe_creation_name}" VALUES (1, "test")')
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()
    from bist_signal_bot.core.exceptions import DataImportAdapterError
    try:
        registry.read_dataframe(db_path, max_rows=1)
        print("Bypassed validation!")
    except DataImportAdapterError as e:
        print(f"Caught: {e}")
    except Exception as e:
        print(f"Other exception: {e}")
