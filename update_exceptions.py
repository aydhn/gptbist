import re

with open("bist_signal_bot/core/exceptions.py", "r") as f:
    content = f.read()

new_exceptions = """
class PatternDetectionError(BistSignalBotError):
    \"\"\"Raised when an error occurs during pattern detection.\"\"\"
    pass

class PatternValidationError(PatternDetectionError):
    \"\"\"Raised when pattern inputs or parameters are invalid.\"\"\"
    pass

class PatternEngineError(PatternDetectionError):
    \"\"\"Raised when there is an error in the pattern engine.\"\"\"
    pass
"""

content += new_exceptions

with open("bist_signal_bot/core/exceptions.py", "w") as f:
    f.write(content)
