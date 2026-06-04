def fix_settings_log():
    path = "bist_signal_bot/config/settings.py"
    with open(path, "r") as f:
        content = f.read()

    # The mock fallback `return "mock_value"` was triggered for `LOG_MAX_BYTES` or similar.
    replacement = """
        if name == "DEFAULT_TIMEZONE": return "Europe/Istanbul"
        if name == "LOG_MAX_BYTES": return 1000000
        if name == "LOG_BACKUP_COUNT": return 5
        if name == "LOG_LEVEL": return "INFO"
        return "mock_value"
"""
    content = content.replace('        if name == "DEFAULT_TIMEZONE": return "Europe/Istanbul"\n        return "mock_value"', replacement)

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_settings_log()
