import re

with open("bist_signal_bot/ml/training/trainer.py", "r") as f:
    content = f.read()

content = content.replace("audit = AuditLogger(get_metadata_dir(self.settings))", "audit = AuditLogger(self.settings, get_metadata_dir(self.settings))")

with open("bist_signal_bot/ml/training/trainer.py", "w") as f:
    f.write(content)
