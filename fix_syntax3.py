def fix_migration():
    path = "bist_signal_bot/release_policy/migrations.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace('lines = ["# Migration Notes\n"]', 'lines = ["# Migration Notes\\n"]')
    with open(path, "w") as f:
        f.write(content)

def fix_deprecations():
    path = "bist_signal_bot/release_policy/deprecations.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace('lines = ["# Deprecation Notices\n"]', 'lines = ["# Deprecation Notices\\n"]')
    with open(path, "w") as f:
        f.write(content)

def fix_changelog3():
    path = "bist_signal_bot/release_policy/changelog.py"
    with open(path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if 'lines.append(f"{e.description}' in line:
            lines[i] = '            lines.append(f"{e.description}\\n")\n'

    with open(path, "w") as f:
        f.writelines(lines)

if __name__ == "__main__":
    fix_migration()
    fix_deprecations()
    fix_changelog3()
