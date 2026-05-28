with open("bist_signal_bot/factors/theme.py", "r") as f:
    content = f.read()

content = content.replace("from typing import List, Optional, Dict", "from typing import List, Optional, Dict, Any")

with open("bist_signal_bot/factors/theme.py", "w") as f:
    f.write(content)
