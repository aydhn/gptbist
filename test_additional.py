with open("bist_signal_bot/cli/parsers.py", "a") as f:
    f.write("\n# Factors CLI parser will be registered here\n")

with open("bist_signal_bot/cli/formatting.py", "a") as f:
    f.write("\n# Factors CLI formatting will be registered here\n")

with open("bist_signal_bot/docs/29_COMMAND_EXAMPLES.md", "a") as f:
    f.write("\n## Factors\n```bash\npython -m bist_signal_bot factors compute ASELS\n```\n")

with open("bist_signal_bot/docs/30_DEVELOPER_GUIDE.md", "a") as f:
    f.write("\n## Factor Engine\nThe factor engine is located in `bist_signal_bot/factors`.\n")

with open("README.md", "a") as f:
    f.write("\n## Factor Exposure & Sector Rotation\nLocal deterministic factor scoring and sector rotation research.\n")

print("Docs updated")
