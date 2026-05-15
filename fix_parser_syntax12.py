with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if i == 869: # 870 is 0-indexed 869
        skip = True

    if skip and line.strip() == "" and i > 890:
        skip = False

    if not skip:
        new_lines.append(line)

# Let's just do it cleanly
with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)
