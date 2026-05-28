import os
def touch_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            pass

touch_file("bist_signal_bot/app/factors_app.py")
