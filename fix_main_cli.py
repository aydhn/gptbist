with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()

content = content.replace("from bist_signal_bot.cli.commands import (", "from bist_signal_bot.cli.commands import (\n    cmd_patterns_list,\n    cmd_patterns_detect,\n    cmd_pattern_features,")
content = content.replace("\"volume-features\": cmd_volume_features,", "\"volume-features\": cmd_volume_features,\n        \"patterns\": lambda a, c: cmd_patterns_list(a, c) if a.patterns_command == 'list' else cmd_patterns_detect(a, c),\n        \"pattern-features\": cmd_pattern_features,")

with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(content)
