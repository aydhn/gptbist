from typing import Any, Dict, List
from bist_signal_bot.macro.models import MacroProxyName

class MacroProxyRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self._proxy_defs = {
            MacroProxyName.USDTRY: {"group": "FX", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.EURTRY: {"group": "FX", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.EURUSD: {"group": "FX", "risk_proxy": False, "higher_is_pressure": False},
            MacroProxyName.GOLD_TRY: {"group": "COMMODITY", "risk_proxy": True, "higher_is_pressure": False},
            MacroProxyName.GOLD_USD: {"group": "COMMODITY", "risk_proxy": True, "higher_is_pressure": False},
            MacroProxyName.BRENT_OIL: {"group": "COMMODITY", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.WTI_OIL: {"group": "COMMODITY", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.CDS_5Y: {"group": "RATES", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.POLICY_RATE: {"group": "RATES", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.BIST100: {"group": "EQUITY", "risk_proxy": False, "higher_is_pressure": False},
            MacroProxyName.BIST30: {"group": "EQUITY", "risk_proxy": False, "higher_is_pressure": False},
            MacroProxyName.BANK_INDEX: {"group": "EQUITY", "risk_proxy": False, "higher_is_pressure": False},
            MacroProxyName.INDUSTRIAL_INDEX: {"group": "EQUITY", "risk_proxy": False, "higher_is_pressure": False},
            MacroProxyName.VIX_PROXY: {"group": "GLOBAL_RISK", "risk_proxy": True, "higher_is_pressure": True},
            MacroProxyName.GLOBAL_RISK_PROXY: {"group": "GLOBAL_RISK", "risk_proxy": True, "higher_is_pressure": True},
        }

    def default_proxies(self) -> List[Dict[str, Any]]:
        return [{"name": name.value, **defs} for name, defs in self._proxy_defs.items()]

    def proxy_definition(self, proxy_name: MacroProxyName) -> Dict[str, Any]:
        return self._proxy_defs.get(proxy_name, {"group": "CUSTOM", "risk_proxy": False, "higher_is_pressure": False})

    def proxy_group(self, proxy_name: MacroProxyName) -> str:
        return self.proxy_definition(proxy_name).get("group", "CUSTOM")

    def is_risk_proxy(self, proxy_name: MacroProxyName) -> bool:
        return self.proxy_definition(proxy_name).get("risk_proxy", False)

    def higher_is_pressure(self, proxy_name: MacroProxyName) -> bool:
        return self.proxy_definition(proxy_name).get("higher_is_pressure", False)
