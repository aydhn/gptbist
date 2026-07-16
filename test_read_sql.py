import sqlite3
import pandas as pd
conn = sqlite3.connect(':memory:')
conn.execute("CREATE TABLE test (a INT)")
try:
    df = pd.read_sql("test", conn)
    print("Success read_sql")
except Exception as e:
    print("Exception read_sql:", type(e), e)
