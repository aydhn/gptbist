
import re

with open("bist_signal_bot/__main__.py", "r") as f:
    content = f.read()

if "elif args.command == 'monitoring':" not in content:
    patch = '''    elif args.command == 'monitoring':
        from bist_signal_bot.cli.commands import run_monitoring_cli
        run_monitoring_cli(args)
'''
    # Find block of elifs and insert
    content = re.sub(r"(    else:\n        parser.print_help\(\))", patch + r"\1", content)

    with open("bist_signal_bot/__main__.py", "w") as f:
        f.write(content)
