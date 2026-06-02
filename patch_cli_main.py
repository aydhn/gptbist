import re
from pathlib import Path

# Patch parsers.py to include add_report_templates_parser in setup_main_parser
p_path = Path("bist_signal_bot/cli/parsers.py")
if p_path.exists():
    c = p_path.read_text()
    if "add_report_templates_parser(subparsers)" not in c:
        c = c.replace(
            "add_data_import_parser(subparsers)",
            "add_data_import_parser(subparsers)\n    add_report_templates_parser(subparsers)"
        )
        p_path.write_text(c)

# Patch main.py or wherever the dispatcher is to route to cmd_report_templates
m_path = Path("bist_signal_bot/__main__.py")
if m_path.exists():
    c = m_path.read_text()
    if "args.command == \"report-templates\":" not in c:
        c = c.replace(
            "elif args.command == \"data-import\":",
            "elif args.command == \"report-templates\":\n        from bist_signal_bot.cli.commands import cmd_report_templates\n        return cmd_report_templates(args, app_context)\n    elif args.command == \"data-import\":"
        )
        m_path.write_text(c)

print("CLI wiring patched.")
