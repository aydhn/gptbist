import subprocess
import sys
import time
import os

MAX_RESTARTS = 3
COOLDOWN_SECONDS = 5

def main():
    script_to_run = sys.argv[1:] if len(sys.argv) > 1 else [sys.executable, "-m", "bist_signal_bot"]

    print(f"Supervisor starting command: {' '.join(script_to_run)}")

    restarts = 0
    while restarts < MAX_RESTARTS:
        print(f"Starting process... (Attempt {restarts + 1}/{MAX_RESTARTS})")

        try:
            process = subprocess.Popen(
                script_to_run,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            process.wait()

            if process.returncode == 0:
                print("Process finished successfully.")
                break
            else:
                print(f"Process exited with error code {process.returncode}.")
        except KeyboardInterrupt:
            print("\nSupervisor received KeyboardInterrupt. Stopping process...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            break
        except Exception as e:
            print(f"Error running process: {e}")

        restarts += 1
        if restarts < MAX_RESTARTS:
            print(f"Restarting in {COOLDOWN_SECONDS} seconds...")
            time.sleep(COOLDOWN_SECONDS)

    if restarts >= MAX_RESTARTS:
        print(f"Maximum restarts ({MAX_RESTARTS}) reached. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
