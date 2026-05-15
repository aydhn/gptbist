with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 448:
        pass # Skip the second `add_quality_parser` call
    else:
        new_lines.append(line)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)
