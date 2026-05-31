import re

with open("bist_signal_bot/__main__.py", "r") as f:
    content = f.read()

if "args.command == 'monitoring'" not in content:
    # Try a different injection strategy since the first one didn't work.

    # We look for the block of elif args.command == 'something' and inject it before the last else.
    # Usually `sys.exit` or `parser.print_help()` is the fallback.

    # Find `parser.print_help()`
    if "parser.print_help()" in content:
        content = content.replace("parser.print_help()", "pass\n    elif args.command == 'monitoring':\n        from bist_signal_bot.cli.commands import run_monitoring_cli\n        run_monitoring_cli(args)\n    else:\n        parser.print_help()")
        with open("bist_signal_bot/__main__.py", "w") as f:
            f.write(content)
