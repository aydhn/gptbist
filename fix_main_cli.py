import re

filepath = "bist_signal_bot/cli/main.py"
with open(filepath, "r") as f:
    content = f.read()

# Add review to commands dict if not there
if '"review":' not in content:
    review_cmd = '        "review": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cli"]).cli(sys.argv[1:], prog_name="bist_signal_bot"),\n'

    # Well wait, click commands use a different structure.
    # Let's just use the argparse trick at the top for review

    argparse_trick = """
    if args_to_parse and args_to_parse[0] == 'review':
        from bist_signal_bot.cli.commands import review
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        review()
        return 0
"""
    content = re.sub(r"(if args_to_parse and args_to_parse\[0\] == 'governance':)", argparse_trick + r"\1", content)

    with open(filepath, "w") as f:
        f.write(content)
