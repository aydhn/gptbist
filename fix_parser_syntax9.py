with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Let's count how many times `subparsers.add_parser("quality"` appears
import re
matches = re.findall(r'subparsers\.add_parser\("quality"', content)
print(f"Found {len(matches)} occurrences")

# We will read line by line and if it's the second occurrence of add_quality_parser
# or something similar we just remove it.
lines = content.split('\n')
new_lines = []
in_first_quality_parser = False
in_second_quality_parser = False
quality_parser_count = 0

for line in lines:
    if "def add_quality_parser(subparsers):" in line:
        quality_parser_count += 1
        if quality_parser_count > 1:
            in_second_quality_parser = True

    if in_second_quality_parser:
        # Stop skipping if we hit the end of the file or another function definition that we want to keep
        # Wait, actually let's just use regular expressions to find all "def add_quality_parser" blocks
        pass
