with open("bist_signal_bot/research/ledger.py", "r") as f:
    content = f.read()

content = content.replace("    ResearchEvent, ResearchEventType,\n", "")

with open("bist_signal_bot/research/ledger.py", "w") as f:
    f.write(content)
