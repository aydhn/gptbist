import sqlite3
import pandas as pd
conn = sqlite3.connect(':memory:')
conn.execute("CREATE TABLE test (a INT)")
try:
    df = pd.read_sql("SELECT * FROM test", conn)
    print("Success read_sql SELECT *")
except Exception as e:
    print("Exception read_sql:", type(e), e)
