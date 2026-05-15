with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def add_quality_parser" in line:
        # Keep the last one
        pass
    if "quality_parser = subparsers.add_parser(\"quality\"" in line:
        pass

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# We will just split and keep the first definition of add_quality_parser
parts = content.split("def add_quality_parser(subparsers):")
if len(parts) > 2:
    new_content = parts[0] + "def add_quality_parser(subparsers):" + parts[1]
    with open("bist_signal_bot/cli/parsers.py", "w") as f:
        f.write(new_content)
