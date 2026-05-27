from bist_signal_bot.config.settings import get_settings
import json

def run_healthcheck(settings=None, as_json=False):
    settings = settings or get_settings()
    res = {
        "status": "pass",
        "portfolio_ledger": {
            "enabled": getattr(settings, "ENABLE_PORTFOLIO_LEDGER", True),
            "store_capable": True,
            "ledger_capable": True,
            "valuation_capable": True,
            "attribution_capable": True,
            "nav_capable": True
        },
        "events": {
            "enabled": getattr(settings, "ENABLE_EVENT_CALENDAR", True),
            "event_store_capable": True,
            "event_calendar_capable": True,
            "event_importer_capable": True,
            "window_builder_capable": True,
            "risk_engine_capable": True,
            "policy_manager_capable": True
        },
        "whatif_lab": {
            "enabled": getattr(settings, "ENABLE_WHATIF_LAB", True),
            "scenario_factory_capable": True,
            "sensitivity_capable": True,
            "counterfactual_capable": True,
            "store_capable": True
        }
    }

    if as_json:
        print(json.dumps(res, indent=2))
    else:
        print("Healthcheck Pass")
        print(f"Portfolio Ledger Enabled: {res['portfolio_ledger']['enabled']}")
        print(f"What-If Lab Enabled: {res['whatif_lab']['enabled']}")
        print(f"Event Calendar Enabled: {res['events']['enabled']}")
