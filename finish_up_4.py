# Verify CLI runs without crash (will likely fail on imports not implemented but structure works)
try:
    import bist_signal_bot.cli.factors_commands
    print("factors_commands loaded")
except Exception as e:
    print(f"Error loading: {e}")
