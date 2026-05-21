import re

filepath = "bist_signal_bot/cli/main.py"
with open(filepath, "r") as f:
    content = f.read()

# Fix the indentation
argparse_trick = """
    if args_to_parse and args_to_parse[0] == 'review':
        from bist_signal_bot.cli.commands import review
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        review()
        return 0

"""
content = re.sub(r'    if args_to_parse and args_to_parse\[0\] == \'review\':.*?(?=    if args_to_parse and args_to_parse\[0\] == \'governance\':)', argparse_trick, content, flags=re.DOTALL)

with open(filepath, "w") as f:
    f.write(content)
