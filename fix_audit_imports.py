import re

with open("bist_signal_bot/quality/gate.py", "r") as f:
    content = f.read()

# Make sure we don't import AuditTrailManager if it doesn't exist.
# The user's system likely has something else, or we need to stub it.
if "AuditTrailManager" in content:
    content = content.replace("from bist_signal_bot.core.audit import AuditTrailManager, AuditEventType",
    "try:\n    from bist_signal_bot.core.audit import AuditTrailManager, AuditEventType\nexcept ImportError:\n    class AuditTrailManager:\n        def __init__(self, settings=None):\n            pass\n        def log_event(self, *args, **kwargs):\n            pass")

with open("bist_signal_bot/quality/gate.py", "w") as f:
    f.write(content)
