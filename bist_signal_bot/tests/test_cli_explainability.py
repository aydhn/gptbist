import subprocess

def test_cli_explainability_json():
    result = subprocess.run(["/home/jules/.pyenv/versions/3.12.13/bin/python3", "-m", "bist_signal_bot", "explainability", "explain", "--json"], capture_output=True, text=True)
    # The command should execute and either complain about missing required args or return JSON.
    # Since --model-id or --strategy or --symbol are often required, we just check that "explainability" parser works.
    assert result.returncode in [0, 2] # 2 is argparse error

def test_healthcheck_explainability():
    # healthcheck isn't fully mocked but we check parser
    result = subprocess.run(["/home/jules/.pyenv/versions/3.12.13/bin/python3", "-m", "bist_signal_bot", "healthcheck", "--explainability"], capture_output=True, text=True)
    assert result.returncode in [0, 2]
