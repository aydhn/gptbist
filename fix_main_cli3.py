import re

filepath = "bist_signal_bot/cli/main.py"
with open(filepath, "r") as f:
    content = f.read()

trick = """    if args_to_parse and args_to_parse[0] == 'review':
        from bist_signal_bot.cli.commands import review
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        review()
        return 0

"""

# Insert before 'if args_to_parse and args_to_parse[0] == 'governance':'
content = content.replace("    if args_to_parse and args_to_parse[0] == 'governance':", trick + "    if args_to_parse and args_to_parse[0] == 'governance':")

with open(filepath, "w") as f:
    f.write(content)
