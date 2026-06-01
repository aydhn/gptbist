with open("bist_signal_bot/config/settings.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_class = False
for line in lines:
    if line.startswith("class Settings("):
        in_class = True

    # Check if we're hitting unindented variables that should be in the class
    if in_class and not line.startswith(" ") and not line.startswith("\n") and not line.startswith("@") and not line.startswith("def ") and not line.startswith("class "):
        # This is an unindented field. Indent it.
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open("bist_signal_bot/config/settings.py", "w") as f:
    f.writelines(new_lines)
