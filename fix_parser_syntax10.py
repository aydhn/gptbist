import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Let's completely remove all definitions of `add_quality_parser`
content = re.sub(r'def add_quality_parser\(subparsers\):.*?def ', 'def ', content, flags=re.DOTALL)
content = re.sub(r'def add_quality_parser\(subparsers\):.*', '', content, flags=re.DOTALL)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
