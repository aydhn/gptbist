with open('bist_signal_bot/data_import/adapters.py', 'r') as f:
    content = f.read()

content = content.replace("re.match(r'^[a-zA-Z0-9_]+$', table_name)", "re.fullmatch(r'^[a-zA-Z0-9_]+$', table_name)")

with open('bist_signal_bot/data_import/adapters.py', 'w') as f:
    f.write(content)
