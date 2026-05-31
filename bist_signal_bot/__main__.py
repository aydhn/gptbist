import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "monitoring":
        from bist_signal_bot.cli_monitoring import run_monitoring_cli
        cmd = sys.argv[2]
        kwargs = {}
        for i in range(3, len(sys.argv)):
            if sys.argv[i].startswith("--"):
                key = sys.argv[i][2:].replace("-", "_")
                if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith("--"):
                    kwargs[key] = sys.argv[i+1]
                else:
                    kwargs[key] = True
        run_monitoring_cli(cmd, **kwargs)
    elif len(sys.argv) > 1 and sys.argv[1] in ["healthcheck", "doctor", "qa", "ops", "reports"]:
        print(f"Mocked integration for {sys.argv[1]} running with args: {sys.argv[2:]}")
    else:
        print("BIST Signal Bot")

if __name__ == "__main__":
    main()
