import re
print(bool(re.match(r'^[a-zA-Z0-9_]+$', 'users\n')))
print(bool(re.match(r'^[a-zA-Z0-9_]+$', 'users\n" --')))
