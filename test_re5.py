import re
print(bool(re.match(r'^[a-zA-Z0-9_]+\Z', 'table\n')))
