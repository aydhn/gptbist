import sqlite3
import pandas as pd
from pathlib import Path

# Create a test DB
db_path = "test2.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# We need to test if re.match('^[a-zA-Z0-9_]+$', ...) is enough
# or if there is a way to bypass it.
malicious_name = 'users\n'
c.execute(f'CREATE TABLE "{malicious_name}" (id INTEGER, name TEXT)')
c.execute(f'INSERT INTO "{malicious_name}" VALUES (1, "test")')
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
