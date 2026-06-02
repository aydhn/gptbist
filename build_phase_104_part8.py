import os
import subprocess

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=False)

print("\n--- Testing CLI Commands ---")
run("python -m bist_signal_bot synthetic-scenarios list")
run("python -m bist_signal_bot synthetic-scenarios list --kind CRASH --json")
run("python -m bist_signal_bot synthetic-scenarios show trend_up_basic_v1")
run("python -m bist_signal_bot synthetic-scenarios show full_pipeline_demo_v1 --json")
run("python -m bist_signal_bot synthetic-scenarios generate --scenario trend_up_basic_v1 --dry-run")
run("python -m bist_signal_bot synthetic-scenarios generate --scenario full_pipeline_demo_v1 --save --json")
run("python -m bist_signal_bot synthetic-scenarios validate --scenario trend_up_basic_v1")
run("python -m bist_signal_bot synthetic-scenarios validate --scenario full_pipeline_demo_v1 --json")
run("python -m bist_signal_bot synthetic-scenarios export --scenario trend_up_basic_v1 --format jsonl --dry-run")
run("python -m bist_signal_bot synthetic-scenarios export --scenario full_pipeline_demo_v1 --format csv --confirm --json")
run("python -m bist_signal_bot synthetic-scenarios stress --scenario crash_rebound_v1")
run("python -m bist_signal_bot synthetic-scenarios stress --scenario macro_stress_v1 --json")
run("python -m bist_signal_bot synthetic-scenarios edge-cases --scenario missing_data_v1")
run("python -m bist_signal_bot synthetic-scenarios edge-cases --scenario schema_drift_v1 --json")
run("python -m bist_signal_bot synthetic-scenarios manifest --scenario full_pipeline_demo_v1")
run("python -m bist_signal_bot synthetic-scenarios manifest --latest --json")
run("python -m bist_signal_bot synthetic-scenarios report")
run("python -m bist_signal_bot synthetic-scenarios report --latest --json")
run("python -m bist_signal_bot synthetic-scenarios config")

run("python -m bist_signal_bot bootstrap demo --scenario full_pipeline_demo_v1 --json")
run("python -m bist_signal_bot orchestrator run --campaign SYNTHETIC_FULL_PIPELINE_CAMPAIGN --dry-run --json")
run("python -m bist_signal_bot healthcheck --synthetic-scenarios")
run("python -m bist_signal_bot doctor --synthetic-scenarios")
run("python -m bist_signal_bot qa release-gate --include-synthetic-scenarios")
run("python -m bist_signal_bot ops readiness --include-synthetic-scenarios")
run("python -m bist_signal_bot reports daily --dry-run --include-synthetic-scenarios")

print("\n--- Running Pytest ---")
run("pytest bist_signal_bot/tests/test_synthetic_scenarios.py -v")
