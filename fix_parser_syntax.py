with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

content = content.replace("def setup_ml_train_parser(subparsers)\n", "def setup_ml_train_parser(subparsers):\n")
content = content.replace("def setup_ml_train_parser(subparsers)    ", "def setup_ml_train_parser(subparsers):\n    ")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
