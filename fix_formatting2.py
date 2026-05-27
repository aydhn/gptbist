file_path = "bist_signal_bot/cli/formatting.py"
with open(file_path, "r") as f:
    content = f.read()

# Fix syntax error
content = content.replace("try:\n    import pandas as pd\\except ImportError:\n    pd = None\n", "try:\n    import pandas as pd\nexcept ImportError:\n    pd = None\n")
with open(file_path, "w") as f:
    f.write(content)
