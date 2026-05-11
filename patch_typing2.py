with open("bist_signal_bot/ml/training/trainer.py", "r") as f:
    content = f.read()

if "from typing import Any" not in content:
    content = "from typing import Any\n" + content

with open("bist_signal_bot/ml/training/trainer.py", "w") as f:
    f.write(content)

with open("bist_signal_bot/ml/training/preprocessing.py", "r") as f:
    content = f.read()

if "from typing import Any" not in content:
    content = "from typing import Any\n" + content

with open("bist_signal_bot/ml/training/preprocessing.py", "w") as f:
    f.write(content)
