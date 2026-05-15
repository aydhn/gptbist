with open("bist_signal_bot/tests/test_quality_coverage.py", "r") as f:
    content = f.read()

content = content.replace("res.stdout = \"Name  Stmts  Miss  Cover\\n-------------------------\\nTOTAL    100    50    50%\"\\n        res.stderr = \"\"", "res.stdout = \"Name  Stmts  Miss  Cover\\n-------------------------\\nTOTAL    100    50    50%\"\n            res.stderr = \"\"")

with open("bist_signal_bot/tests/test_quality_coverage.py", "w") as f:
    f.write(content)
