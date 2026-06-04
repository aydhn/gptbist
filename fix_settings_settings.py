def fix_settings():
    path = "bist_signal_bot/config/settings.py"
    with open(path, "r") as f:
        content = f.read()

    # The existing codebase expects 'settings' as an exported object.
    content += "\nsettings = _settings\n"

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_settings()
