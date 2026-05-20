with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "from bist_signal_bot.cli.ensemble_commands import setup_ensemble_parser" in line:
        new_lines.append(line)
        new_lines.append("from bist_signal_bot.cli.stress_cmd import add_stress_parsers\n")
    elif "setup_ensemble_parser(subparsers)" in line:
        new_lines.append(line)
        new_lines.append("    add_stress_parsers(subparsers)\n")
    else:
        new_lines.append(line)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)

with open("bist_signal_bot/cli/main.py", "r") as f:
    main_c = f.read()

import re
if "handle_stress_command" not in main_c:
    main_c = main_c.replace('from bist_signal_bot.cli.ensemble_commands import handle_ensemble_command',
    'from bist_signal_bot.cli.ensemble_commands import handle_ensemble_command\nfrom bist_signal_bot.cli.stress_cmd import handle_stress_command')
    main_c = re.sub(r'("ensemble": lambda a, c:.*?handle_ensemble_command\(a\),)', r'\1\n        "stress": lambda a, c: __import__("bist_signal_bot.cli.stress_cmd", fromlist=["handle_stress_command"]).handle_stress_command(a, c.settings),', main_c)
    with open("bist_signal_bot/cli/main.py", "w") as f:
        f.write(main_c)
