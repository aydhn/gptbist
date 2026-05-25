from pathlib import Path
from typing import Any

from bist_signal_bot.explainability.feature_attribution import FeatureAttributionEngine
from bist_signal_bot.explainability.indicator_state import IndicatorStateExplainer
from bist_signal_bot.explainability.rule_trace import RuleTraceBuilder
from bist_signal_bot.explainability.ml_explain import MLExplainer
from bist_signal_bot.explainability.ensemble_explain import EnsembleExplainer
from bist_signal_bot.explainability.risk_explain import RiskExplainer
from bist_signal_bot.explainability.execution_explain import ExecutionExplainer
from bist_signal_bot.explainability.history_context import HistoryContextExplainer
from bist_signal_bot.explainability.evidence_card import EvidenceCardBuilder
from bist_signal_bot.explainability.decision_trace import DecisionTraceBuilder
from bist_signal_bot.explainability.storage import ExplainabilityStore

def create_feature_attribution_engine(settings: Any = None) -> FeatureAttributionEngine:
    return FeatureAttributionEngine(settings=settings)

def create_indicator_state_explainer(settings: Any = None) -> IndicatorStateExplainer:
    return IndicatorStateExplainer(settings=settings)

def create_rule_trace_builder(settings: Any = None) -> RuleTraceBuilder:
    return RuleTraceBuilder(settings=settings)

def create_ml_explainer(settings: Any = None) -> MLExplainer:
    return MLExplainer(settings=settings)

def create_ensemble_explainer(settings: Any = None) -> EnsembleExplainer:
    return EnsembleExplainer(settings=settings)

def create_risk_explainer(settings: Any = None) -> RiskExplainer:
    return RiskExplainer(settings=settings)

def create_execution_explainer(settings: Any = None) -> ExecutionExplainer:
    return ExecutionExplainer(settings=settings)

def create_history_context_explainer(settings: Any = None, base_dir: Path | None = None) -> HistoryContextExplainer:
    return HistoryContextExplainer(settings=settings, base_dir=base_dir)

def create_evidence_card_builder(settings: Any = None, base_dir: Path | None = None) -> EvidenceCardBuilder:
    return EvidenceCardBuilder(settings=settings, base_dir=base_dir)

def create_decision_trace_builder(settings: Any = None) -> DecisionTraceBuilder:
    return DecisionTraceBuilder(settings=settings)

def create_explainability_store(settings: Any = None, base_dir: Path | None = None) -> ExplainabilityStore:
    return ExplainabilityStore(settings=settings, base_dir=base_dir)
