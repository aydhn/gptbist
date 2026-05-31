import re
path = "bist_signal_bot/__main__.py"
with open(path, "r") as f:
    content = f.read()

hook = """
        if cmd == "model-registry":
            import argparse
            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="command")
            add_model_registry_parser(sub)

            from bist_signal_bot.config.settings import get_settings
            args = parser.parse_args(sys.argv[1:])
            execute_model_registry_command(args, get_settings())
"""

if "model-registry" not in content:
    content = content.replace("    print(\"BIST Signal Bot OK\")", hook + "\n    print(\"BIST Signal Bot OK\")")

with open(path, "w") as f:
    f.write(content)
