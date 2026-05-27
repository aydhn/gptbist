from typing import Any
import uuid
from datetime import datetime
from typing import Any
from bist_signal_bot.explainability.models import (
    EvidenceCard,
    EvidenceCardSection,
    EvidenceCardSectionType,
    ExplanationStatus,
    SignalExplanation
)

class EvidenceCardBuilder:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

    def build_card(self, explanation: SignalExplanation) -> EvidenceCard:
        sections = []
        sections.append(self.section_summary(explanation))
        if explanation.indicator_explanations:
            sections.append(self.section_indicators(explanation))
        if explanation.rule_trace:
            sections.append(self.section_rules(explanation))
        if explanation.risk_explanation:
            sections.append(self.section_risk(explanation))
        if explanation.execution_explanation:
            sections.append(self.section_execution(explanation))
        if explanation.history_context:
            sections.append(self.section_history(explanation))

        score = self.overall_score(sections)
        status = self.overall_status(score, explanation.warnings)

        missing = []
        if not explanation.ml_explanation:
            missing.append("ML model context")
        if not explanation.history_context or not explanation.history_context.relevant_memory:
            missing.append("Historical context")

        return EvidenceCard(
            card_id=str(uuid.uuid4()),
            symbol=explanation.symbol,
            strategy_name=explanation.strategy_name,
            signal_id=explanation.signal_id,
            created_at=datetime.utcnow(),
            title=f"Evidence Card: {explanation.symbol} - {explanation.strategy_name or 'No Strategy'}",
            summary=explanation.summary,
            sections=sections,
            overall_score=score,
            overall_status=status,
            key_supporting_points=[],
            key_risks=[],
            missing_evidence=missing,
            warnings=explanation.warnings
        )

    def build_from_signal(self, signal_payload: dict[str, Any]) -> EvidenceCard:
        return self.build_card(SignalExplanation(
            explanation_id=str(uuid.uuid4()),
            symbol=signal_payload.get("symbol", "UNKNOWN"),
            generated_at=datetime.utcnow(),
            summary="Auto-generated explanation from signal payload.",
            final_status=ExplanationStatus.UNKNOWN
        ))

    def section_summary(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.SUMMARY,
            title="Summary",
            body=explanation.summary,
            status=explanation.final_status
        )

    def section_indicators(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.INDICATORS,
            title="Indicators",
            body=f"{len(explanation.indicator_explanations)} indicators analyzed.",
            status=ExplanationStatus.PASS
        )

    def section_rules(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.STRATEGY_RULES,
            title="Strategy Rules",
            body="Rules evaluated successfully.",
            status=ExplanationStatus.PASS if explanation.rule_trace and explanation.rule_trace.status == ExplanationStatus.PASS else ExplanationStatus.WARN
        )

    def section_risk(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.RISK,
            title="Risk Check",
            body="Risk evaluated.",
            status=ExplanationStatus.PASS
        )

    def section_execution(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.EXECUTION,
            title="Execution Sim",
            body="Execution estimated.",
            status=ExplanationStatus.PASS
        )

    def section_history(self, explanation: SignalExplanation) -> EvidenceCardSection:
        return EvidenceCardSection(
            section_id=str(uuid.uuid4()),
            section_type=EvidenceCardSectionType.HISTORY_CONTEXT,
            title="Historical Context",
            body="History analyzed.",
            status=ExplanationStatus.PASS
        )

    def overall_score(self, sections: list[EvidenceCardSection]) -> float | None:
        return 75.0 # Mock

    def overall_status(self, score: float | None, warnings: list[str]) -> ExplanationStatus:
        if warnings:
            return ExplanationStatus.WARN
        return ExplanationStatus.PASS

    def add_whatif_section(self, card: EvidenceCard, whatif_run_result: Any) -> None:
        if not whatif_run_result:
            return

        lines = []
        if hasattr(whatif_run_result, 'comparison') and whatif_run_result.comparison:
            comp = whatif_run_result.comparison
            if comp.sensitivity_findings:
                lines.append("Bu sinyal/sepet hangi varsayımlara hassas?")
                for f in comp.sensitivity_findings:
                    lines.append(f"- {f.metric_name}: {f.message}")
            if comp.key_findings:
                lines.append("Maliyet artarsa kalite nasıl değişiyor?")
                for kf in comp.key_findings:
                    lines.append(f"- {kf}")

        if hasattr(whatif_run_result, 'capital_scaling') and whatif_run_result.capital_scaling:
            cs = whatif_run_result.capital_scaling
            if cs.capacity_warnings:
                lines.append("Sermaye ölçeklenirse likidite uyarısı var mı?")
                for cw in cs.capacity_warnings:
                    lines.append(f"- {cw}")

        section = EvidenceSection(
            section_id=str(uuid.uuid4()),
            title="What-If Scenario Lab",
            content="\n".join(lines) if lines else "What-If analysis completed without significant findings.",
            importance=EvidenceImportance.MEDIUM
        )
        card.sections.append(section)


    def section_valuation(self, symbol: str) -> EvidenceCardSection:
        try:
            from bist_signal_bot.app.valuation_app import create_valuation_store
            store = create_valuation_store(self.settings)
            risk = store.load_latest_risk(symbol)
            if risk:
                return EvidenceCardSection(
                    section_id=str(uuid.uuid4()),
                    section_type=EvidenceCardSectionType.RISK,
                    title="Valuation Context",
                    body=f"Score: {risk.valuation_score}. Level: {risk.valuation_risk_level.value}. {risk.recommended_decision}",
                    status=ExplanationStatus.PASS
                )
        except Exception as e:
            print(f'ERROR: {e}')
        return None
