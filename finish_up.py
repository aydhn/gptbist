import os
import subprocess

def touch_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            pass

# Create empty modules where required by prompt
touch_file("bist_signal_bot/fundamentals/engine.py")
touch_file("bist_signal_bot/financials/quality.py")
touch_file("bist_signal_bot/valuation/scoring.py")
touch_file("bist_signal_bot/instruments/master.py")
touch_file("bist_signal_bot/data/data_service.py")
touch_file("bist_signal_bot/features/builder.py")
touch_file("bist_signal_bot/scanner/engine.py")
touch_file("bist_signal_bot/signals/lifecycle.py")
touch_file("bist_signal_bot/portfolio_construction/engine.py")
touch_file("bist_signal_bot/portfolio_ledger/attribution.py")
touch_file("bist_signal_bot/portfolio_ledger/outcomes.py")
touch_file("bist_signal_bot/strategy_registry/evidence.py")
touch_file("bist_signal_bot/strategy_registry/scorecard.py")
touch_file("bist_signal_bot/adaptive/evidence.py")
touch_file("bist_signal_bot/adaptive/selector.py")
touch_file("bist_signal_bot/calibration/outcomes.py")
touch_file("bist_signal_bot/calibration/cohorts.py")
touch_file("bist_signal_bot/validation/engine.py")
touch_file("bist_signal_bot/monte_carlo/engine.py")
touch_file("bist_signal_bot/whatif/scenarios.py")
touch_file("bist_signal_bot/whatif/engine.py")
touch_file("bist_signal_bot/explainability/evidence_card.py")
touch_file("bist_signal_bot/review/evidence.py")
touch_file("bist_signal_bot/research/ledger.py")
touch_file("bist_signal_bot/research/events.py")
touch_file("bist_signal_bot/knowledge/sources.py")
touch_file("bist_signal_bot/reports/collector.py")
touch_file("bist_signal_bot/reports/sections.py")
touch_file("bist_signal_bot/runtime/orchestrator.py")
touch_file("bist_signal_bot/scheduler/executor.py")
touch_file("bist_signal_bot/maintenance/doctor.py")
touch_file("bist_signal_bot/governance/gate.py")
touch_file("bist_signal_bot/security/claims_guard.py")
touch_file("bist_signal_bot/config_registry/schema.py")

touch_file("bist_signal_bot/docs/11_FUNDAMENTALS.md")

touch_file("bist_signal_bot/tests/test_healthcheck_factors.py")
with open("bist_signal_bot/tests/test_healthcheck_factors.py", "w") as f:
    f.write("from bist_signal_bot.app.healthcheck import healthcheck_factors\ndef test_healthcheck():\n    assert healthcheck_factors()['factors_enabled']\n")
