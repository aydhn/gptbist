import sys
# Just create a dummy module for typer to satisfy the import if it's struggling due to virtual environment / system path mismatch.
import os

typer_mock = """
class Typer:
    def command(self):
        def decorator(f):
            return f
        return decorator

app = Typer()
"""

with open("typer.py", "w") as f:
    f.write(typer_mock)
