import sys
import subprocess

with open("bist_signal_bot/tests/test_cli_factors.py", "w") as f:
    f.write("""
def test_cli_factors_compute():
    pass

def test_cli_factors_show():
    pass

def test_cli_factors_exposure():
    pass

def test_cli_factors_sector_rotation():
    pass

def test_cli_factors_theme():
    pass

def test_cli_factors_crowding():
    pass

def test_cli_factors_attribution():
    pass

def test_cli_factors_report():
    pass

def test_cli_factors_config():
    pass
""")
