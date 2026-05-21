import os

filepath = "bist_signal_bot/core/exceptions.py"
with open(filepath, "r") as f:
    content = f.read()

if "class ReviewError(BistBotError):" not in content:
    exceptions = """

class ReviewError(BistBotError):
    pass

class ReviewValidationError(ReviewError):
    pass

class ReviewInboxError(ReviewError):
    pass

class ReviewChecklistError(ReviewError):
    pass

class ReviewThesisError(ReviewError):
    pass

class ReviewDecisionError(ReviewError):
    pass

class ReviewJournalError(ReviewError):
    pass

class ReviewFollowupError(ReviewError):
    pass

class ReviewStorageError(ReviewError):
    pass
"""
    content += exceptions
    with open(filepath, "w") as f:
        f.write(content)
