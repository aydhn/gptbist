import re

path = "bist_signal_bot/cli/commands.py"
try:
    with open(path, "r") as f:
        content = f.read()

    if "model_registry" not in content.lower():
        # Hook into setup_parsers
        import_stmt = "from bist_signal_bot.cli.model_registry import add_model_registry_parser, execute_model_registry_command\n"

        # Add to parsers
        parser_hook = "    add_model_registry_parser(subparsers)\n"

        # Add to execution
        exec_hook = """    elif args.command == "model-registry":
        execute_model_registry_command(args, settings)
"""
        # This is a bit tricky without knowing exact structure, let's create a minimal bist_signal_bot/cli/commands.py if missing or patch

        # Actually it's probably better to just create a dummy if it doesn't exist, since the system is vast.
        # But we must modify the root main.py or __main__.py to register our new CLI.
        pass
except FileNotFoundError:
    pass

# Modify main.py
main_path = "bist_signal_bot/__main__.py"
try:
    with open(main_path, "r") as f:
        main_content = f.read()

    if "model-registry" not in main_content:
        # Add to imports
        imports = "from bist_signal_bot.cli.model_registry import add_model_registry_parser, execute_model_registry_command\n"
        main_content = imports + main_content

        # Add to subparsers
        if "subparsers =" in main_content:
            idx = main_content.find("subparsers =")
            next_line_idx = main_content.find("\n", idx)
            main_content = main_content[:next_line_idx+1] + "    add_model_registry_parser(subparsers)\n" + main_content[next_line_idx+1:]

        # Add to dispatch
        if "if args.command ==" in main_content:
            dispatch = """    if args.command == "model-registry":
        execute_model_registry_command(args, settings)
    el"""
            main_content = main_content.replace("    if args.command ==", dispatch)

    with open(main_path, "w") as f:
        f.write(main_content)
except Exception as e:
    print(e)
