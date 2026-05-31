with open("bist_signal_bot/__main__.py", "r") as f:
    content = f.read()

patch = '''
        if cmd == "monitoring":
            import argparse
            from bist_signal_bot.cli.commands import run_monitoring_cli
            parser = argparse.ArgumentParser()
            parser.add_argument("monitoring")
            parser.add_argument("monitoring_cmd")
            parser.add_argument("--object-type", default=None)
            parser.add_argument("--object-id", default=None)
            parser.add_argument("--save", action="store_true")
            parser.add_argument("--json", action="store_true")
            parser.add_argument("strategy_id", nargs="?", default=None)
            parser.add_argument("model_id", nargs="?", default=None)
            parser.add_argument("feature_set_id", nargs="?", default=None)
            parser.add_argument("--champion", default=None)
            parser.add_argument("--challenger", default=None)
            parser.add_argument("--unacknowledged", action="store_true")
            parser.add_argument("--ack", default=None)
            parser.add_argument("--note", default=None)
            parser.add_argument("watch_cmd", nargs="?", default=None)
            parser.add_argument("--reason", default=None)
            parser.add_argument("--latest", action="store_true")
            parser.add_argument("--limit", type=int, default=10)
            args, _ = parser.parse_known_args(sys.argv[1:])
            run_monitoring_cli(args)
            sys.exit(0)
'''

# Find a good place to insert, right after `if len(sys.argv) > 1:`
if 'cmd == "monitoring"' not in content:
    content = content.replace('        if cmd == "data-catalog":', patch + '\n        if cmd == "data-catalog":')
    with open("bist_signal_bot/__main__.py", "w") as f:
        f.write(content)
