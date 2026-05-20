import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import pandas as pd

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.audit import AuditLogger, AuditEvent
from bist_signal_bot.ensemble.models import (
    EnsembleRequest, EnsembleResult, ConsensusSignal, EnsembleExplanation, EnsembleMode
)
from bist_signal_bot.ensemble.collectors import SignalVoteCollector
from bist_signal_bot.ensemble.scoring import EnsembleScorer
from bist_signal_bot.ensemble.conflicts import ConflictResolver
from bist_signal_bot.ensemble.explainability import EnsembleExplainer
from bist_signal_bot.ensemble.weights import EnsembleWeightManager
from bist_signal_bot.ensemble.storage import EnsembleStore

logger = logging.getLogger(__name__)

class EnsembleEngine:
    def __init__(
        self,
        collector: SignalVoteCollector,
        scorer: EnsembleScorer,
        conflict_resolver: ConflictResolver,
        explainer: EnsembleExplainer,
        weight_manager: EnsembleWeightManager,
        store: EnsembleStore,
        settings: Optional[Settings] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.collector = collector
        self.scorer = scorer
        self.conflict_resolver = conflict_resolver
        self.explainer = explainer
        self.weight_manager = weight_manager
        self.store = store
        self.settings = settings or get_settings()
        self.audit = audit_logger or AuditLogger(self.settings)

    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "EnsembleEngine":
        s = settings or get_settings()
        wm = EnsembleWeightManager(s)
        st = EnsembleStore(s)
        cr = ConflictResolver()
        ex = EnsembleExplainer()
        sc = EnsembleScorer(s, cr, ex)
        co = SignalVoteCollector(settings=s)

        return cls(co, sc, cr, ex, wm, st, s)

    def run(self, request: EnsembleRequest) -> EnsembleResult:
        start_time = time.time()

        mode_val = getattr(request.mode, "value", str(request.mode))

        try:
            self.audit.log_event(AuditEvent(
                event_type="ENSEMBLE_RUN_STARTED",
                message=f"Starting ensemble run for {len(request.symbols)} symbols",
                metadata={"mode": mode_val, "source": request.source}
            ))
        except Exception:
            pass

        # Prep weights
        base_weights = request.weights or self.weight_manager.load_weights()
        if not base_weights:
            base_weights = self.weight_manager.default_weights()

        signals = []
        for sym in request.symbols:
            try:
                # 1. Collect
                votes = self.collector.collect_votes(sym, request)

                # 2. Regime adjustment (mocked for now, assuming regime engine handles it)
                regime_name = "TRENDING" # placeholder
                w = self.weight_manager.weights_for_regime(regime_name, base_weights)

                # 3. Score
                as_of = request.as_of_date or pd.Timestamp.now()
                sig = self.scorer.score_consensus(sym, votes, w, request.mode, as_of)
                signals.append(sig)

            except Exception as e:
                logger.error(f"Error processing ensemble for {sym}: {e}")

        # 4. Rank
        ranked = self.scorer.rank_consensus(signals)

        # Split
        approved = [s for s in ranked if s.decision.value == "APPROVED_RESEARCH"]
        rejected = [s for s in ranked if s.decision.value in ("REJECTED", "SKIPPED", "ERROR")]

        res = EnsembleResult(
            request=request,
            consensus_signals=signals,
            ranked_signals=ranked,
            rejected_signals=rejected,
            elapsed_seconds=time.time() - start_time
        )

        # 5. Save
        if request.save_output and getattr(self.settings, "ENSEMBLE_SAVE_OUTPUTS", False):
            try:
                res.output_files = self.store.save_result(res)
            except Exception as e:
                logger.warning(f"Could not save ensemble result: {e}")

        try:
            self.audit.log_event(AuditEvent(
                event_type="ENSEMBLE_RUN_COMPLETED",
                message=f"Ensemble run completed for {len(request.symbols)} symbols",
                metadata={
                    "consensus_count": len(res.consensus_signals),
                    "approved_count": len(approved),
                    "no_real_order_sent": True
                }
            ))
        except Exception:
            pass

        return res

    def explain(self, symbol: str, request: EnsembleRequest) -> EnsembleExplanation:
        req = request.model_copy()
        req.symbols = [symbol]
        req.save_output = False
        res = self.run(req)

        if not res.consensus_signals:
            raise ValueError(f"Could not generate consensus for {symbol}")

        return res.consensus_signals[0].explanation

    def run_for_signal(self, signal_candidate: Any, request: EnsembleRequest) -> ConsensusSignal:
        req = request.model_copy()
        req.symbols = [signal_candidate.symbol]
        req.save_output = False
        res = self.run(req)
        if not res.consensus_signals:
            raise ValueError(f"Could not generate consensus for {signal_candidate.symbol}")
        return res.consensus_signals[0]

    def build_request_from_settings(self, symbols: list[str]) -> EnsembleRequest:
        strats = [s.strip() for s in getattr(self.settings, "ENSEMBLE_DEFAULT_STRATEGIES", "").split(",") if s.strip()]
        return EnsembleRequest(
            symbols=symbols,
            strategy_names=strats,
            timeframe=self.settings.DEFAULT_TIMEFRAME,
            mode=EnsembleMode(getattr(self.settings, "ENSEMBLE_DEFAULT_MODE", "METADATA_ONLY")),
            include_ml=getattr(self.settings, "ENSEMBLE_INCLUDE_ML", False),
            include_regime=getattr(self.settings, "ENSEMBLE_INCLUDE_REGIME", False),
            include_risk=getattr(self.settings, "ENSEMBLE_INCLUDE_RISK", False),
            include_fundamentals=getattr(self.settings, "ENSEMBLE_INCLUDE_FUNDAMENTALS", False),
            include_breadth=getattr(self.settings, "ENSEMBLE_INCLUDE_BREADTH", False),
            include_adaptive=getattr(self.settings, "ENSEMBLE_INCLUDE_ADAPTIVE", False),
            save_output=getattr(self.settings, "ENSEMBLE_SAVE_OUTPUTS", False)
        )
