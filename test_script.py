import re
import sqlite3
import pandas as pd
from pathlib import Path

# Create a test DB
db_path = "test.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# We need to test if re.match('^[a-zA-Z0-9_]+$', ...) is enough
# or if there is a way to bypass it.
print(re.match(r'^[a-zA-Z0-9_]+$', 'table_name'))
print(re.match(r'^[a-zA-Z0-9_]+$', 'table"name'))
print(re.match(r'^[a-zA-Z0-9_]+$', 'users"; DROP TABLE users; --'))

conn.close()
