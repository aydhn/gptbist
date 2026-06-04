def fix_formatter():
    path = "bist_signal_bot/notifications/formatter.py"
    if not __import__('os').path.exists(path):
        with open(path, "w") as f:
            f.write("class NotificationFormatter:\n    pass\n")
    else:
        with open(path, "r") as f:
            content = f.read()
        if "class NotificationFormatter" not in content:
            content += "\nclass NotificationFormatter:\n    pass\n"
            with open(path, "w") as f:
                f.write(content)

if __name__ == "__main__":
    fix_formatter()
