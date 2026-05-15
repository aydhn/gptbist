with open("bist_signal_bot/main.py", "r") as f:
    content = f.read()

# Make sure main.py has `quality` as a valid command choice if there's some manual check
# Actually, the error is 'Unknown command: quality' which means it parses it but doesn't handle it?
# Ah! In bist_signal_bot/main.py, does it pass the command directly, or is there a hardcoded list?
