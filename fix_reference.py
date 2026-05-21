import re

with open("bist_signal_bot/drift/reference.py", "r") as f:
    content = f.read()

content = content.replace("window.dict(default=str)", "window.model_dump(mode='json')")

with open("bist_signal_bot/drift/reference.py", "w") as f:
    f.write(content)
