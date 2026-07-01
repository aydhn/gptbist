🔒 Fix SQL injection vulnerability in Data Import Adapter

🎯 **What:** The `read_preview` and `read_dataframe` methods in `LocalImportAdapterRegistry` for the SQLite format contained a SQL injection vulnerability. Specifically, they formatted the `table_name` and `max_rows` dynamically directly into the raw SQL string using f-strings (e.g. `f"SELECT * FROM {table_name} LIMIT {max_rows}"`).

⚠️ **Risk:** A maliciously crafted SQLite database file with specially formulated table names could alter the query execution context leading to local SQL injection. An attacker could bypass limits or trigger alternative read access.

🛡️ **Solution:**
1. **Identifier Escaping**: Applied standard SQLite identifier escaping for the `table_name` by duplicating internal double-quotes and wrapping the name in double-quotes (`'"{}"'.format(table_name.replace('"', '""'))`).
2. **Parameterization**: Modified both queries to correctly use parameterized bindings (e.g., `LIMIT ?` with `params=(max_rows,)`) for the user-controlled integer parameter.
3. **Tests added**: Created robust tests mimicking malicious table injections which now successfully parse without throwing SQLite parsing errors.
