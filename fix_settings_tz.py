def fix_tz():
    path = "bist_signal_bot/config/settings.py"
    with open(path, "r") as f:
        content = f.read()

    # The issue is DEFAULT_TIMEZONE returns "mock_value". Let's fix our mock.
    content = content.replace('        return "mock_value"', '        if name == "DEFAULT_TIMEZONE": return "Europe/Istanbul"\n        return "mock_value"')

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_tz()
