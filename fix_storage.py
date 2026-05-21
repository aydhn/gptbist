import re

with open("bist_signal_bot/drift/storage.py", "r") as f:
    content = f.read()

content = content.replace("result.dict(default=str)", "result.model_dump(mode='json')")
content = content.replace("r.dict(default=str)", "r.model_dump(mode='json')")

with open("bist_signal_bot/drift/storage.py", "w") as f:
    f.write(content)
