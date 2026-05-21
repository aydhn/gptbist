import re

with open("bist_signal_bot/drift/model_drift.py", "r") as f:
    content = f.read()

if "import numpy as np" not in content:
    content = content.replace("import pandas as pd", "import pandas as pd\nimport numpy as np")

with open("bist_signal_bot/drift/model_drift.py", "w") as f:
    f.write(content)
