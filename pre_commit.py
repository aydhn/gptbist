import subprocess
print("Running pre-commit steps...")
subprocess.run(["python", "-m", "pytest"])
subprocess.run(["python", "-m", "bist_signal_bot"])
print("Pre-commit steps completed.")
