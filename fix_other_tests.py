import re

with open("bist_signal_bot/research/ledger.py", "r") as f:
    content = f.read()

# Add ResearchEvent to models import if not there
if "ResearchEvent" not in content and "def log_whatif_run" in content:
    content = content.replace("from bist_signal_bot.research.models import ResearchLog", "from bist_signal_bot.research.models import ResearchLog, ResearchEvent")
    with open("bist_signal_bot/research/ledger.py", "w") as f:
        f.write(content)
