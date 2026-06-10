import sys
import os

def main():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    try:
        from bist_signal_bot.app.healthcheck import run_healthcheck
        print("Running full healthcheck...")
        run_healthcheck()
    except ImportError as e:
        print(f"Could not import main healthcheck. Running basic smoke test... ({e})")
        if not os.path.exists("bist_signal_bot/__main__.py"):
            print("ERROR: bist_signal_bot module not found.")
            sys.exit(1)
        if not os.path.exists("pyproject.toml"):
            print("ERROR: Run this from the root directory.")
            sys.exit(1)

        try:
            import pandas
            import pydantic
            print("Basic dependencies found.")
        except ImportError as e:
            print(f"ERROR: Missing dependency - {e}")
            sys.exit(1)

    print("Healthcheck/Smoke Test Passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
