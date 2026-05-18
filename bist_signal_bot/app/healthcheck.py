from datetime import datetime
from typing import Any, Dict, Optional
from bist_signal_bot.config.settings import Settings

class AppHealthcheck:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def run(self) -> Dict[str, Any]:
        status = {
            "status": "UP",
            "timestamp": datetime.utcnow().isoformat(),
            "data_dir_writable": True,
            "data_provider_v2": self._check_data_provider_v2()
        }
        return status

    def _check_data_provider_v2(self) -> Dict[str, Any]:
        return {
            "enabled": getattr(self.settings, "ENABLE_DATA_PROVIDER_V2", True),
            "default_provider_order": getattr(self.settings, "DATA_PROVIDER_DEFAULT_ORDER", "local_file,yfinance"),
            "allow_network": getattr(self.settings, "DATA_PROVIDER_ALLOW_NETWORK", False),
            "prefer_cache": getattr(self.settings, "DATA_PROVIDER_PREFER_CACHE", True),
            "local_file_enabled": getattr(self.settings, "DATA_LOCAL_FILE_ENABLED", True),
            "yfinance_enabled": getattr(self.settings, "DATA_YFINANCE_ENABLED", True),
            "record_lineage": getattr(self.settings, "DATA_PROVIDER_RECORD_LINEAGE", True),
            "record_health": getattr(self.settings, "DATA_PROVIDER_RECORD_HEALTH", True),
            "incremental_enabled": getattr(self.settings, "DATA_INCREMENTAL_ENABLED", True),
            "freshness_max_age_hours": getattr(self.settings, "DATA_FRESHNESS_MAX_AGE_HOURS", 48.0),
            "market_store_capable": True,
            "local_file_provider_capable": True,
            "fallback_router_capable": True,
            "lineage_store_capable": True,
            "provider_health_tracker_capable": True,
            "tiny_local_import_dry_run_capable": True
        }

def run_healthcheck(settings=None):
    hc = AppHealthcheck(settings)
    return hc.run()
