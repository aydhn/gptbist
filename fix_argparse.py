import re
with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()

# Add to the argparse block
new_content = re.sub(
    r"parser\.add_subparsers\(dest=\"command\", help=\"Mevcut Komutlar\"\)",
    r"parser.add_subparsers(dest=\"command\", help=\"Mevcut Komutlar\")\n    factors_parser = subparsers.add_parser('factors', help='Factor Analysis')\n    factors_parser.add_argument('subcmd', nargs='?', default='compute')",
    content
)

with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(new_content)
