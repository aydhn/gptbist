import sqlite3
import pandas as pd
from pathlib import Path

# Create a test DB
db_path = "test3.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

malicious_name = 'users\n" --'
c.execute(f'CREATE TABLE "{malicious_name.replace("\"", "\"\"")}" (id INTEGER, name TEXT)')
c.execute(f'INSERT INTO "{malicious_name.replace("\"", "\"\"")}" VALUES (1, "test")')
conn.commit()
conn.close()

from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.core.exceptions import DataImportAdapterError
registry = LocalImportAdapterRegistry()

try:
    print(registry.read_dataframe(Path(db_path)))
    print("Bypassed validation!")
except DataImportAdapterError as e:
    print(f"Caught: {e}")
except Exception as e:
    print(f"Other error: {e}")
