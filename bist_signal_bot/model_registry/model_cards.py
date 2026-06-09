import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelCardError
from bist_signal_bot.model_registry.models import (
    ModelCard, ModelRecord, ModelValidationSummary, ModelCalibrationSummary, ModelGovernanceStatus
)


class ModelCardBuilder:
    def __init__(self, settings: Settings | None = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.store = store

    def default_intended_use(self, model: ModelRecord) -> str:
        return f"This {model.model_kind.value} model is intended for local research and simulation purposes to generate experimental signals for symbol ranking and analysis."

    def default_not_intended_use(self, model: ModelRecord) -> str:
        return "This model is NOT intended for real order execution, live trading, or providing investment advice. It is strictly a research tool."

    def known_limitations(self, model: ModelRecord) -> list[str]:
        limitations = [
            "Assumes historical patterns will repeat, which is not guaranteed.",
            "May suffer from regime changes and market shocks not present in training data.",
            "Does not account for real-world slippage, exact transaction costs, or liquidity constraints."
        ]
        if model.model_kind.value in ["CLASSIFIER", "REGRESSOR"]:
            limitations.append("Statistical predictions are probabilistic and individual predictions will often be wrong.")
        return limitations

    def risk_notes(self, model: ModelRecord) -> list[str]:
        return [
            "Model decay: Performance may degrade over time requiring retraining.",
            "Overfitting risk: High validation scores do not guarantee future out-of-sample performance.",
            "Data latency: Features based on delayed or restated data may introduce look-ahead bias if not perfectly aligned."
        ]

    def validate_card(self, card: ModelCard) -> list[str]:
        issues = []
        n_i_u = card.not_intended_use.lower()
        if "real order execution" not in n_i_u or "investment advice" not in n_i_u:
            issues.append("not_intended_use must explicitly forbid 'real order execution' and 'investment advice'")
        if not card.input_features:
            issues.append("input_features cannot be empty")
        return issues

    def build_card(self, model: ModelRecord, validation: ModelValidationSummary | None = None,
                   calibration: ModelCalibrationSummary | None = None,
                   input_features: list[str] | None = None,
                   training_data_summary: str | None = None,
                   intended_use: str | None = None,
                   not_intended_use: str | None = None) -> ModelCard:

        val_summary = ""
        gov_status = ModelGovernanceStatus.UNKNOWN

        if validation:
            val_summary = f"Method: {validation.validation_method}. Status: {validation.status.value}. "
            if validation.metrics:
                val_summary += f"Metrics: {validation.metrics}"
            gov_status = validation.status

        cal_summary = ""
        if calibration:
            cal_summary = f"Method: {calibration.calibration_method}. Status: {calibration.status.value}. "
            if calibration.reliability_score is not None:
                cal_summary += f"Reliability: {calibration.reliability_score:.2f}"

        # Aggregate status logic could be more complex, but for the builder we just take the lowest
        if validation and calibration:
            if validation.status == ModelGovernanceStatus.BLOCKED or calibration.status == ModelGovernanceStatus.BLOCKED:
                gov_status = ModelGovernanceStatus.BLOCKED
            elif validation.status == ModelGovernanceStatus.FAIL or calibration.status == ModelGovernanceStatus.FAIL:
                gov_status = ModelGovernanceStatus.FAIL
            elif validation.status == ModelGovernanceStatus.WATCH or calibration.status == ModelGovernanceStatus.WATCH:
                gov_status = ModelGovernanceStatus.WATCH

        card = ModelCard(
            card_id=f"card_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model.model_id,
            model_name=model.model_name,
            version=model.version,
            created_at=datetime.now(timezone.utc),
            intended_use=intended_use or self.default_intended_use(model),
            not_intended_use=not_intended_use or self.default_not_intended_use(model),
            input_features=input_features or ["Feature list not provided"],
            training_data_summary=training_data_summary or f"Datasets: {', '.join(model.dataset_refs) if model.dataset_refs else 'Unknown'}",
            validation_summary=val_summary or "No validation summary provided.",
            calibration_summary=cal_summary or "No calibration summary provided.",
            known_limitations=self.known_limitations(model),
            risk_notes=self.risk_notes(model),
            governance_status=gov_status
        )

        issues = self.validate_card(card)
        if issues:
            self.logger.warning(f"Model card validation issues: {issues}")
            card.warnings.extend(issues)

        return card

    def render_markdown(self, card: ModelCard) -> str:
        lines = [
            f"# Model Card: {card.model_name} (v{card.version})",
            "",
            f"**Card ID:** {card.card_id}",
            f"**Model ID:** {card.model_id}",
            f"**Created At:** {card.created_at.isoformat()}",
            f"**Governance Status:** {card.governance_status.value}",
            "",
            "## Intended Use",
            card.intended_use,
            "",
            "## Not Intended Use (WARNING)",
            card.not_intended_use,
            "",
            "## Input Features",
            *[f"- {feat}" for feat in card.input_features],
            "",
            "## Training Data",
            card.training_data_summary,
            "",
            "## Validation",
            card.validation_summary,
            "",
            "## Calibration",
            card.calibration_summary,
            "",
            "## Known Limitations",
            *[f"- {lim}" for lim in card.known_limitations],
            "",
            "## Risk Notes",
            *[f"- {risk}" for risk in card.risk_notes],
            "",
            "---",
            f"**Disclaimer:** {card.disclaimer}"
        ]


        if card.supported_explanation_methods or card.top_feature_importance:
            lines.extend([
                "",
                "## Explainability Details"
            ])
            if card.supported_explanation_methods:
                lines.append(f"**Supported Methods:** {', '.join(card.supported_explanation_methods)}")
            if card.top_feature_importance:
                lines.append("**Top Features:**")
                for k, v in card.top_feature_importance.items():
                    lines.append(f"- {k}: {v:.4f}")
            if card.explanation_caveats:
                lines.append("**Caveats:**")
                for cav in card.explanation_caveats:
                    lines.append(f"- {cav}")
            if card.unsupported_method_warnings:
                lines.append("**Unsupported Warnings:**")
                for w in card.unsupported_method_warnings:
                    lines.append(f"- {w}")

        if card.warnings:
            lines.extend([
                "",
                "## Warnings",
                *[f"- {w}" for w in card.warnings]
            ])

        return "\n".join(lines)
