import re

with open("bist_signal_bot/__main__.py", "r") as f:
    content = f.read()

if "elif args.command == 'monitoring':" not in content:
    patch = '''    elif args.command == 'monitoring':
        from bist_signal_bot.cli.commands import run_monitoring_cli
        run_monitoring_cli(args)
'''
    content = content.replace("    else:\n        parser.print_help()", patch + "    else:\n        parser.print_help()")
    with open("bist_signal_bot/__main__.py", "w") as f:
        f.write(content)
