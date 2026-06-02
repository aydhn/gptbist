import os
from pathlib import Path

ex_path = Path("bist_signal_bot/core/exceptions.py")
content = ex_path.read_text()

if "class DataImportError(" in content:
    content = content.replace("class DataImportError(Exception):", "class DataImportError(BistSignalBotError):")

if "class DataImportAdapterError(" not in content:
    print("WARNING missing exceptions")

ex_path.write_text(content)
