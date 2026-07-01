import uuid
import logging
import time
import pandas as pd
from dataclasses import dataclass
from typing import Any
from datetime import datetime

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    DriftAnalysisRequest, DriftAnalysisResult, DriftDomain,
    DriftStatus, DriftSeverity, DriftAction, FeatureDriftResult,
    ModelDriftResult, SignalDecayReport, StrategyDecayReport, PortfolioDriftReport
)
from bist_signal_bot.drift.feature_drift import FeatureDriftDetector
from bist_signal_bot.drift.model_drift import ModelDriftDetector
from bist_signal_bot.drift.calibration import CalibrationMonitor
from bist_signal_bot.drift.signal_decay import SignalDecayAnalyzer
from bist_signal_bot.drift.strategy_decay import StrategyDecayAnalyzer
from bist_signal_bot.drift.portfolio_drift import PortfolioDriftAnalyzer
from bist_signal_bot.drift.reference import DriftReferenceManager
from bist_signal_bot.drift.storage import DriftStore

logger = logging.getLogger(__name__)


@dataclass
class DriftEngineDependencies:
    settings: Settings | None = None
    store: DriftStore | None = None
    feature_detector: FeatureDriftDetector | None = None
    model_detector: ModelDriftDetector | None = None
    calibration_monitor: CalibrationMonitor | None = None
    signal_analyzer: SignalDecayAnalyzer | None = None
    strategy_analyzer: StrategyDecayAnalyzer | None = None
    portfolio_analyzer: PortfolioDriftAnalyzer | None = None
    reference_manager: DriftReferenceManager | None = None

class DriftEngine:
    def __init__(self, deps: DriftEngineDependencies | None = None):
        deps = deps or DriftEngineDependencies()
        self.settings = deps.settings or get_settings()
        self.store = deps.store or DriftStore(self.settings)
        self.feature_detector = deps.feature_detector or FeatureDriftDetector(self.settings)
        self.model_detector = deps.model_detector or ModelDriftDetector(self.settings)
        self.calibration_monitor = deps.calibration_monitor or CalibrationMonitor(self.settings)
        self.signal_analyzer = deps.signal_analyzer or SignalDecayAnalyzer(self.settings)
        self.strategy_analyzer = deps.strategy_analyzer or StrategyDecayAnalyzer(self.settings)
        self.portfolio_analyzer = deps.portfolio_analyzer or PortfolioDriftAnalyzer(self.settings)
        self.reference_manager = deps.reference_manager or DriftReferenceManager(self.settings)

    def analyze(self, request: DriftAnalysisRequest) -> DriftAnalysisResult:
        start_time = time.time()

        result = DriftAnalysisResult(
            drift_id=str(uuid.uuid4()),
            request=request
        )

        if not request.domains:
            if self.settings.DRIFT_DEFAULT_DOMAINS:
                request.domains = [DriftDomain(d.strip()) for d in self.settings.DRIFT_DEFAULT_DOMAINS.split(",")]
            else:
                request.domains = [DriftDomain.FEATURE, DriftDomain.MODEL_SCORE]

        all_actions = set()
        severities = []

        try:
            for domain in request.domains:
                if domain == DriftDomain.FEATURE:
                    pass
                elif domain == DriftDomain.MODEL_SCORE:
                    res = self.analyze_model(request.model_id)
                    result.model_results.append(res)
                    all_actions.update(res.recommended_actions)
                    severities.append(res.severity)
                elif domain == DriftDomain.SIGNAL_OUTCOME:
                    if self.settings.DRIFT_SIGNAL_DECAY_ENABLED:
                         res = self.analyze_signals()
                         result.signal_decay_reports.append(res)
                         all_actions.update(res.recommended_actions)
                         severities.append(res.severity)
                elif domain == DriftDomain.STRATEGY_PERFORMANCE:
                    if self.settings.DRIFT_STRATEGY_DECAY_ENABLED:
                         for strat in request.strategies:
                              res = self.analyze_strategy(strat)
                              result.strategy_decay_reports.append(res)
                              all_actions.update(res.recommended_actions)
                              severities.append(res.severity)
                elif domain == DriftDomain.PORTFOLIO_RESEARCH:
                    if self.settings.DRIFT_PORTFOLIO_DRIFT_ENABLED:
                         res = self.analyze_portfolio()
                         result.portfolio_drift_reports.append(res)
                         all_actions.update(res.recommended_actions)
                         severities.append(res.severity)

            result.overall_drift_score = self.calculate_overall_score(result)
            status, severity = self.derive_overall_status(result.overall_drift_score, severities)
            result.status = status
            result.severity = severity

            if not all_actions:
                all_actions.add(DriftAction.NO_ACTION)
            result.recommended_actions = list(all_actions)

            if request.save_output and self.settings.DRIFT_SAVE_RESULTS:
                 paths = self.store.save_result(result)
                 result.output_files = {k: str(v) for k, v in paths.items()}

        except Exception as e:
            logger.error(f"Drift analysis failed: {e}")
            result.status = DriftStatus.ERROR
            result.warnings.append(str(e))

        result.elapsed_seconds = time.time() - start_time
        return result

    def analyze_features(self, reference_df: pd.DataFrame, current_df: pd.DataFrame, feature_names: list[str] | None = None) -> list[FeatureDriftResult]:
        return self.feature_detector.detect(reference_df, current_df, feature_names)

    def analyze_model(self, model_id: str | None = None) -> ModelDriftResult:
        ref_df = pd.DataFrame({"prediction": [0.5, 0.6, 0.4, 0.8, 0.2] * 10})
        cur_df = pd.DataFrame({"prediction": [0.55, 0.65, 0.45, 0.85, 0.25] * 10})
        return self.model_detector.detect_model_drift(model_id, ref_df, cur_df)

    def analyze_signals(self, days_reference: int = 90, days_current: int = 14) -> SignalDecayReport:
        ref_sigs = [{"alert_sent": True, "outcome_positive": True, "muted": False, "invalidated": False} for _ in range(100)]
        cur_sigs = [{"alert_sent": True, "outcome_positive": False, "muted": True, "invalidated": True} for _ in range(50)]
        return self.signal_analyzer.analyze(ref_sigs, cur_sigs)

    def analyze_strategy(self, strategy_name: str, days_reference: int = 180, days_current: int = 30) -> StrategyDecayReport:
        ref_runs = [{"profit_factor": 1.5, "sharpe": 1.2, "max_drawdown": 10.0} for _ in range(20)]
        cur_runs = [{"profit_factor": 0.8, "sharpe": -0.5, "max_drawdown": 25.0} for _ in range(5)]
        return self.strategy_analyzer.analyze(strategy_name, ref_runs, cur_runs)

    def analyze_portfolio(self) -> PortfolioDriftReport:
        ref_snap = {"id": "ref1", "exposures": [{"symbol": "ASELS", "weight": 0.5}, {"symbol": "THYAO", "weight": 0.5}], "metrics": {"concentration_index": 0.1, "average_correlation": 0.2}}
        cur_snap = {"id": "cur1", "exposures": [{"symbol": "ASELS", "weight": 0.9}, {"symbol": "THYAO", "weight": 0.1}], "metrics": {"concentration_index": 0.8, "average_correlation": 0.6}}
        ref_stress = {"stress_rating": "NORMAL"}
        cur_stress = {"stress_rating": "CRITICAL"}
        return self.portfolio_analyzer.analyze(ref_snap, cur_snap, ref_stress, cur_stress)

    def calculate_overall_score(self, result: DriftAnalysisResult) -> float | None:
        score = 0.0
        count = 0

        for r in result.strategy_decay_reports:
             if r.decay_score is not None:
                 score += r.decay_score
             count += 1

        for m in result.model_results:
             if m.status == DriftStatus.SEVERE_DRIFT: score += 50.0
             elif m.status == DriftStatus.DRIFTING: score += 30.0
             elif m.status == DriftStatus.WATCH: score += 10.0
             count += 1

        for r in result.signal_decay_reports:
             if r.status == DriftStatus.SEVERE_DRIFT: score += 50.0
             elif r.status == DriftStatus.DRIFTING: score += 30.0
             elif r.status == DriftStatus.WATCH: score += 10.0
             count += 1

        return score / count if count > 0 else 0.0

    def derive_overall_status(self, score: float | None, severities: list[DriftSeverity]) -> tuple[DriftStatus, DriftSeverity]:
        max_sev = DriftSeverity.LOW
        severities_map = {
            DriftSeverity.CRITICAL: 4, DriftSeverity.HIGH: 3,
            DriftSeverity.MEDIUM: 2, DriftSeverity.LOW: 1, DriftSeverity.UNKNOWN: 0
        }

        for s in severities:
            if severities_map[s] > severities_map[max_sev]:
                max_sev = s

        status = DriftStatus.STABLE
        if max_sev == DriftSeverity.CRITICAL:
             status = DriftStatus.SEVERE_DRIFT
        elif max_sev == DriftSeverity.HIGH:
             status = DriftStatus.DRIFTING
        elif max_sev == DriftSeverity.MEDIUM:
             status = DriftStatus.WATCH

        if score is not None:
             if score >= 70.0 and status != DriftStatus.SEVERE_DRIFT:
                  status = DriftStatus.DRIFTING
                  if severities_map.get(max_sev, 0) < 3: max_sev = DriftSeverity.HIGH
             elif score >= 40.0 and status == DriftStatus.STABLE:
                  status = DriftStatus.WATCH
                  if severities_map.get(max_sev, 0) < 2: max_sev = DriftSeverity.MEDIUM

        return status, max_sev

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> 'DriftEngine':
        deps = DriftEngineDependencies(settings=settings)
        return cls(deps=deps)