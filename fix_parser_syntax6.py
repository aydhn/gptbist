with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Wait, conflicting subparser: quality. That means it was added somewhere else?
# Let's check for add_parser("quality")
import re
count = len(re.findall(r'add_parser\("quality"', content))
print(f"Found {count} calls to add_parser('quality')")

if count > 1:
    print("Conflicting parsers found, need to remove the first one.")
    # Usually it's in the large list of parser configurations early in the file or somewhere else.
    # We will find the first occurrence and remove it, or just let python do it.
