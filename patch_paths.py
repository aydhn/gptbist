import re

with open("bist_signal_bot/storage/paths.py", "r") as f:
    content = f.read()

if "get_performance_dir" not in content:
    performance_path = """
def get_performance_dir(settings: Optional[Settings] = None) -> Path:
    s = settings or Settings()
    d = DATA_DIR / getattr(s, "PERFORMANCE_DIR_NAME", "performance")
    d.mkdir(parents=True, exist_ok=True)
    return d
"""
    content += performance_path
    with open("bist_signal_bot/storage/paths.py", "w") as f:
        f.write(content)
