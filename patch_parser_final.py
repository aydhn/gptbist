import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Add to build_parser
if "add_security_parser(subparsers)" in content and "add_quality_parser(subparsers)" not in content:
    content = content.replace(
        "add_security_parser(subparsers)",
        "add_security_parser(subparsers)\n    add_quality_parser(subparsers)"
    )

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)

with open("bist_signal_bot/main.py", "r") as f:
    main_content = f.read()

if "from bist_signal_bot.cli.commands import" in main_content and "handle_quality_command" not in main_content:
    main_content = main_content.replace(
        "handle_security_command",
        "handle_security_command,\n    handle_quality_command"
    )

if "elif args.command == \"security\":" in main_content and "elif args.command == \"quality\":" not in main_content:
    main_content = main_content.replace(
        "elif args.command == \"security\":\n        handle_security_command(args, settings)",
        "elif args.command == \"security\":\n        handle_security_command(args, settings)\n    elif args.command == \"quality\":\n        handle_quality_command(args, settings)"
    )

with open("bist_signal_bot/main.py", "w") as f:
    f.write(main_content)
