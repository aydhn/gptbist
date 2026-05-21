filepath = "bist_signal_bot/core/exceptions.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("class ReviewError(BistBotError):", "class ReviewError(BistSignalBotError):")

with open(filepath, "w") as f:
    f.write(content)
