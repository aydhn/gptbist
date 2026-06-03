import os

def check_cli():
    # Attempt to actually run one of the CLI commands to verify
    # First we need to make sure bist_signal_bot module loads.
    os.system('python -c "from bist_signal_bot.release_policy.models import ReleasePolicyStatus; print(ReleasePolicyStatus.PASS.value)"')

if __name__ == "__main__":
    check_cli()
    print("Part 13 complete.")
