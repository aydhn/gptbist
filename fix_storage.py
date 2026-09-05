import re

with open("bist_signal_bot/portfolio_ledger/storage.py", "r") as f:
    content = f.read()

# Remove unused imports
content = content.replace("from typing import Any\nfrom pydantic import BaseModel\nfrom datetime import datetime, timezone", "from pydantic import BaseModel")

with open("bist_signal_bot/portfolio_ledger/storage.py", "w") as f:
    f.write(content)
