import re
with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()

# Make sure we don't cause import errors
content = re.sub(r'from bist_signal_bot\.cli\.factors_commands import factors_cli', '', content)

with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(content)

with open("bist_signal_bot/cli/main.py", "a") as f:
    f.write("\nfrom bist_signal_bot.cli.factors_commands import factors_cli\n")
    f.write("try:\n")
    f.write("    if 'cli' in globals():\n")
    f.write("        cli.add_command(factors_cli)\n")
    f.write("except Exception:\n")
    f.write("    pass\n")
