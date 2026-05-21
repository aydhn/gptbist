import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import uuid

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import AdaptiveEvidence, AdaptiveEvidenceType
from bist_signal_bot.storage.paths import (
    get_optimization_dir,
    get_backtest_results_dir,
    get_paper_dir,
    get_scans_dir,
    get_ml_models_dir,
    get_runtime_runs_dir
)

class AdaptiveEvidenceCollector:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)

    def collect_from_optimization(self, strategy_name: str | None = None, symbol: str | None = None, limit: int = 20) -> list[AdaptiveEvidence]:
        try:
            opt_dir = get_optimization_dir(self.settings)
            if not opt_dir.exists():
                return []

            evidence_items = []
            files = sorted(opt_dir.glob("**/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for file in files:
                if len(evidence_items) >= limit:
                    break

                if "backtest" in str(file) or "paper" in str(file):
                    continue

                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if strategy_name and data.get("strategy_name") != strategy_name:
                        continue
                    if symbol and data.get("symbol") != symbol:
                        continue

                    if "best_params" in data and "metrics" in data:
                        score = self._extract_score(data.get("metrics", {}))

                        evidence_items.append(
                            AdaptiveEvidence(
                                evidence_id=f"opt_{uuid.uuid4().hex[:8]}",
                                evidence_type=AdaptiveEvidenceType.OPTIMIZATION,
                                symbol=data.get("symbol"),
                                strategy_name=data.get("strategy_name"),
                                params=data.get("best_params", {}),
                                score=score,
                                confidence=min(100.0, float(data.get("metrics", {}).get("total_trades", 0)) * 2),
                                metrics=data.get("metrics", {}),
                                source_path=str(file.name),
                                generated_at=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc),
                                metadata={"trial_count": data.get("trial_count", 0)}
                            )
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to parse optimization file {file}: {e}")

            return evidence_items
        except Exception as e:
            self.logger.warning(f"Error collecting optimization evidence: {e}")
            return []

    def collect_from_backtests(self, strategy_name: str | None = None, symbol: str | None = None, limit: int = 20) -> list[AdaptiveEvidence]:
        try:
            bt_dir = get_backtest_results_dir(self.settings)
            if not bt_dir.exists():
                return []

            evidence_items = []
            files = sorted(bt_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for file in files:
                if len(evidence_items) >= limit:
                    break

                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if strategy_name and data.get("strategy_name") != strategy_name:
                        continue
                    if symbol and data.get("symbol") != symbol:
                        continue

                    metrics = data.get("metrics", {})
                    score = self._extract_score(metrics)

                    evidence_items.append(
                        AdaptiveEvidence(
                            evidence_id=f"bt_{uuid.uuid4().hex[:8]}",
                            evidence_type=AdaptiveEvidenceType.BACKTEST,
                            symbol=data.get("symbol"),
                            strategy_name=data.get("strategy_name"),
                            params=data.get("strategy_params", {}),
                            score=score,
                            confidence=min(100.0, float(metrics.get("total_trades", 0)) * 2),
                            metrics=metrics,
                            source_path=str(file.name),
                            generated_at=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to parse backtest file {file}: {e}")

            return evidence_items
        except Exception as e:
            self.logger.warning(f"Error collecting backtest evidence: {e}")
            return []

    def collect_from_paper(self, account_id: str | None = None, limit: int = 100) -> list[AdaptiveEvidence]:
        try:
            paper_dir = get_paper_dir(self.settings)
            if not paper_dir.exists():
                return []

            evidence_items = []
            for acc_dir in paper_dir.iterdir():
                if not acc_dir.is_dir():
                    continue
                if account_id and acc_dir.name != account_id:
                    continue
                ledger_file = acc_dir / "ledger.json"
                if not ledger_file.exists():
                    continue
                try:
                    with open(ledger_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    trades = data.get("trades", [])
                    if trades:
                        evidence_items.append(
                            AdaptiveEvidence(
                                evidence_id=f"paper_{uuid.uuid4().hex[:8]}",
                                evidence_type=AdaptiveEvidenceType.PAPER_TRADING,
                                symbol=None,
                                strategy_name=data.get("strategy_name", "mixed"),
                                params={},
                                score=self._paper_score(trades),
                                confidence=min(100.0, len(trades) * 5.0),
                                metrics={"total_trades": len(trades), "balance": data.get("balance", 0)},
                                source_path=str(ledger_file.name),
                                generated_at=datetime.now(timezone.utc)
                            )
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to parse paper ledger {ledger_file}: {e}")

            return evidence_items[:limit]
        except Exception as e:
            self.logger.warning(f"Error collecting paper evidence: {e}")
            return []

    def collect_from_scans(self, strategy_name: str | None = None, limit: int = 20) -> list[AdaptiveEvidence]:
        try:
            scans_dir = get_scans_dir(self.settings)
            if not scans_dir.exists():
                return []

            evidence_items = []
            files = sorted(scans_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for file in files:
                if len(evidence_items) >= limit:
                    break
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    matches = len(data.get("matches", []))
                    evidence_items.append(
                        AdaptiveEvidence(
                            evidence_id=f"scan_{uuid.uuid4().hex[:8]}",
                            evidence_type=AdaptiveEvidenceType.SCANNER_HISTORY,
                            symbol=None,
                            strategy_name=data.get("strategy_name", "unknown"),
                            params=data.get("params", {}),
                            score=min(100.0, matches * 10.0),
                            confidence=50.0,
                            metrics={"matches": matches, "universe_size": data.get("universe_size", 0)},
                            source_path=str(file.name),
                            generated_at=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to parse scan file {file}: {e}")
            return evidence_items
        except Exception as e:
            self.logger.warning(f"Error collecting scanner evidence: {e}")
            return []

    def collect_from_ml_registry(self, limit: int = 20) -> list[AdaptiveEvidence]:
        try:
            models_dir = get_ml_models_dir(self.settings)
            if not models_dir.exists():
                return []

            evidence_items = []
            files = sorted(models_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for file in files:
                if len(evidence_items) >= limit:
                    break
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    metrics = data.get("metrics", {})
                    acc = metrics.get("accuracy", metrics.get("f1_score", 0.0))
                    evidence_items.append(
                        AdaptiveEvidence(
                            evidence_id=f"ml_{uuid.uuid4().hex[:8]}",
                            evidence_type=AdaptiveEvidenceType.ML_MODEL,
                            symbol=data.get("symbol"),
                            strategy_name=data.get("strategy_name", "ml_filter"),
                            params=data.get("model_params", {}),
                            score=acc * 100.0 if acc <= 1.0 else acc,
                            confidence=min(100.0, data.get("sample_count", 0) / 100.0),
                            metrics=metrics,
                            source_path=str(file.name),
                            generated_at=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc),
                            metadata={"model_id": data.get("model_id")}
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to parse ML model file {file}: {e}")
            return evidence_items
        except Exception as e:
            self.logger.warning(f"Error collecting ML evidence: {e}")
            return []

    def collect_from_regime(self, symbols: list[str] | None = None) -> list[AdaptiveEvidence]:
        return []

    def collect_from_runtime_performance(self, limit: int = 20) -> list[AdaptiveEvidence]:
        try:
            runs_dir = get_runtime_runs_dir(self.settings)
            if not runs_dir.exists():
                return []

            evidence_items = []
            files = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for file in files:
                if len(evidence_items) >= limit:
                    break
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    success = data.get("status") == "COMPLETED"
                    evidence_items.append(
                        AdaptiveEvidence(
                            evidence_id=f"run_{uuid.uuid4().hex[:8]}",
                            evidence_type=AdaptiveEvidenceType.RUNTIME_PERFORMANCE,
                            symbol=None,
                            strategy_name=None,
                            params={},
                            score=100.0 if success else 0.0,
                            confidence=80.0,
                            metrics={"duration": data.get("duration", 0)},
                            source_path=str(file.name),
                            generated_at=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to parse runtime file {file}: {e}")
            return evidence_items
        except Exception as e:
            self.logger.warning(f"Error collecting runtime evidence: {e}")
            return []

    def collect_all(self, symbols: list[str], strategies: list[str]) -> list[AdaptiveEvidence]:
        all_evidence = []
        all_evidence.extend(self.collect_from_optimization(limit=50))
        all_evidence.extend(self.collect_from_backtests(limit=50))
        all_evidence.extend(self.collect_from_paper(limit=10))
        all_evidence.extend(self.collect_from_scans(limit=20))
        all_evidence.extend(self.collect_from_ml_registry(limit=20))
        all_evidence.extend(self.collect_from_runtime_performance(limit=10))

        filtered = []
        for e in all_evidence:
            if e.symbol and e.symbol not in symbols and symbols:
                continue
            if e.strategy_name and e.strategy_name not in strategies and e.strategy_name != "ml_filter":
                continue
            filtered.append(e)
        return filtered

    def _extract_score(self, metrics: dict[str, Any]) -> float:
        pf = float(metrics.get("profit_factor", 1.0) or 1.0)
        sharpe = float(metrics.get("sharpe_ratio", 0.0) or 0.0)
        win_rate = float(metrics.get("win_rate", 0.5) or 0.5)
        score = (min(3.0, pf) / 3.0 * 40) + (max(0.0, min(3.0, sharpe)) / 3.0 * 30) + (win_rate * 30)
        return max(0.0, min(100.0, score))

    def _paper_score(self, trades: list[dict[str, Any]]) -> float:
        if not trades:
            return 50.0
        wins = sum(1 for t in trades if float(t.get("pnl", 0)) > 0)
        win_rate = wins / len(trades)
        return max(0.0, min(100.0, win_rate * 100))
def get_drift_evidence(engine):
    latest = engine.store.load_latest_result()
    if not latest:
         return None
    return {
         "drift_id": latest.drift_id,
         "status": latest.status.value,
         "severity": latest.severity.value,
         "recommended_actions": [a.value for a in latest.recommended_actions]
    }
