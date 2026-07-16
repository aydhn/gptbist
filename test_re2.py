import re
print(bool(re.match(r'^[a-zA-Z0-9_]+$', 'table_name')))
print(bool(re.match(r'^[a-zA-Z0-9_]+$', 'table_name\nDROP TABLE')))
