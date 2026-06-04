import re

def fix_main():
    path = "bist_signal_bot/__main__.py"
    with open(path, "r") as f:
        content = f.read()

    # Add import
    import_stmt = "from bist_signal_bot.cli.release_policy_cli import setup_release_policy_parser, handle_release_policy_command\n"
    if "setup_release_policy_parser" not in content:
        content = import_stmt + content

    # Inject parser setup
    parser_setup = "    setup_release_policy_parser(subparsers)\n"
    if "setup_release_policy_parser(subparsers)" not in content:
        content = content.replace("    add_plugins_parser(subparsers)\n", "    add_plugins_parser(subparsers)\n" + parser_setup)

    # Inject handler
    handler = """    elif args.cmd == "release-policy":
        # The args object needs rp_command since the dest in setup_release_policy_parser is rp_command
        # But wait, our custom parser might have conflicted with the root parser dest
        handle_release_policy_command(args)
        return
"""
    if "args.cmd == \"release-policy\"" not in content:
        content = content.replace("    elif args.cmd:", handler + "    elif args.cmd:")

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_main()
