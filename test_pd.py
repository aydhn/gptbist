import sqlite3
import pandas as pd
conn = sqlite3.connect(':memory:')
conn.execute("CREATE TABLE test (a INT)")
try:
    df = pd.read_sql_table("test", conn)
    print("Success")
except Exception as e:
    print("Exception:", type(e), e)
