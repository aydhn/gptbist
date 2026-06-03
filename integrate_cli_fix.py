import re

def inject_parser():
    # Inject into parsers.py
    path = "bist_signal_bot/cli/parsers.py"
    with open(path, "r") as f:
        content = f.read()

    if "setup_release_policy_parser" not in content:
        # Append the import and the call at the bottom. In a real system, we might find the exact
        # place where subparsers are defined, but let's just create a dummy function if needed,
        # or append the parser setup. Actually, parsers.py usually defines setup_main_parser.

        # Let's find "def setup_main_parser(subparsers):" and inject our setup call.
        if "def setup_main_parser(" in content:
            # simple replacement
            content = content.replace("def setup_main_parser(subparsers):",
                                      "from bist_signal_bot.cli.release_policy_cli import setup_release_policy_parser\\n\\ndef setup_main_parser(subparsers):\\n    setup_release_policy_parser(subparsers)")
        else:
            # fallback
            content += "\nfrom bist_signal_bot.cli.release_policy_cli import setup_release_policy_parser\n"
        with open(path, "w") as f:
            f.write(content)

def inject_commands():
    path = "bist_signal_bot/cli/commands.py"
    with open(path, "r") as f:
        content = f.read()

    if "handle_release_policy_command" not in content:
        content += "\nfrom bist_signal_bot.cli.release_policy_cli import handle_release_policy_command\n"
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    inject_parser()
    inject_commands()
