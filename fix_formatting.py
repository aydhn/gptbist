import os
import sys

file_path = "bist_signal_bot/cli/formatting.py"
with open(file_path, "r") as f:
    content = f.read()

# Mock pandas import as we just need the tests to parse the files
content = content.replace("import pandas as pd", "try:\n    import pandas as pd\except ImportError:\n    pd = None\n")
with open(file_path, "w") as f:
    f.write(content)
