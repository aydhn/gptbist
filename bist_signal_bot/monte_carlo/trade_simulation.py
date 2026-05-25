from typing import Any
import logging

class TradeSimulationAdapter:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("bist_signal_bot.monte_carlo.trade_simulation")

    def trades_from_backtest_result(self, backtest_result: Any) -> list[dict[str, Any]]:
        trades = []
        if not hasattr(backtest_result, "trades") or not backtest_result.trades:
            return []

        for t in backtest_result.trades:
            trade_dict = getattr(t, "__dict__", t) if not isinstance(t, dict) else t.copy()
            norm = self._normalize_trade(trade_dict)
            if norm:
                trades.append(norm)
        return trades

    def returns_from_backtest_result(self, backtest_result: Any, use_net: bool = True) -> list[float]:
        trades = self.trades_from_backtest_result(backtest_result)
        key = "net_return_pct" if use_net else "gross_return_pct"
        return [t.get(key, 0.0) for t in trades]

    def trades_from_paper_ledger(self, ledger: Any) -> list[dict[str, Any]]:
        trades = []
        entries = getattr(ledger, "entries", ledger) if not isinstance(ledger, list) else ledger
        for entry in entries:
            entry_dict = getattr(entry, "__dict__", entry) if not isinstance(entry, dict) else entry.copy()
            if entry_dict.get("status") in ("CLOSED", "COMPLETED"):
                norm = self._normalize_trade(entry_dict)
                if norm:
                    trades.append(norm)
        return trades

    def portfolio_returns_from_basket_result(self, result: Any) -> list[float]:
        if hasattr(result, "basket_returns") and result.basket_returns:
            return list(result.basket_returns)
        if hasattr(result, "returns") and result.returns:
            return list(result.returns)
        if isinstance(result, dict) and "returns" in result:
            return list(result["returns"])
        return []

    def _normalize_trade(self, raw_trade: dict[str, Any]) -> dict[str, Any] | None:
        try:
            # Fallback to gross if net is missing
            gross = raw_trade.get("return_pct", raw_trade.get("gross_return_pct", 0.0))
            net = raw_trade.get("net_return_pct")

            if net is None:
                self.logger.warning("Trade is missing net_return_pct, falling back to gross.")
                net = gross

            return {
                "entry_date": raw_trade.get("entry_date", raw_trade.get("entry_time")),
                "exit_date": raw_trade.get("exit_date", raw_trade.get("exit_time")),
                "gross_return_pct": float(gross),
                "net_return_pct": float(net),
                "cost": float(raw_trade.get("cost", 0.0)),
                "symbol": raw_trade.get("symbol", "UNKNOWN"),
                "strategy_name": raw_trade.get("strategy_name", "UNKNOWN")
            }
        except Exception as e:
            self.logger.error(f"Failed to normalize trade: {e}")
            return None
