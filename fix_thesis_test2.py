filepath = "bist_signal_bot/tests/test_review_thesis.py"
with open(filepath, "r") as f:
    content = f.read()

# Make main_thesis longer than counter_thesis
content = content.replace('"Good trend"', '"Good trend, moving averages are aligning nicely."')

with open(filepath, "w") as f:
    f.write(content)
