import re

with open("bist_signal_bot/drift/reporting.py", "r") as f:
    content = f.read()

content = content.replace("result.dict(default=str)", "result.model_dump(mode='json')")
content = content.replace("report.dict(default=str)", "report.model_dump(mode='json')")
content = content.replace("m.dict(default=str)", "m.model_dump(mode='json')")

with open("bist_signal_bot/drift/reporting.py", "w") as f:
    f.write(content)
