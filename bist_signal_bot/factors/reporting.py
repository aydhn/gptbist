
import pandas as pd
from typing import List, Dict, Any
from bist_signal_bot.factors.models import (
    FactorInputSnapshot, FactorScore, FactorExposure, SectorRotationScore,
    ThemeDefinition, ThemeExposure, FactorCrowdingAssessment, FactorAttributionItem, FactorReport
)

def factor_input_to_dict(input: FactorInputSnapshot) -> Dict[str, Any]: return input.__dict__
def factor_score_to_dict(score: FactorScore) -> Dict[str, Any]: return score.__dict__
def factor_exposure_to_dict(exposure: FactorExposure) -> Dict[str, Any]: return exposure.__dict__
def sector_rotation_to_dict(score: SectorRotationScore) -> Dict[str, Any]: return score.__dict__
def theme_definition_to_dict(theme: ThemeDefinition) -> Dict[str, Any]: return theme.__dict__
def theme_exposure_to_dict(exposure: ThemeExposure) -> Dict[str, Any]: return exposure.__dict__
def crowding_to_dict(assessment: FactorCrowdingAssessment) -> Dict[str, Any]: return assessment.__dict__
def factor_attribution_to_dict(item: FactorAttributionItem) -> Dict[str, Any]: return item.__dict__
def factor_report_to_dict(report: FactorReport) -> Dict[str, Any]: return report.__dict__

def factor_scores_to_dataframe(scores: List[FactorScore]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in scores])

def sector_rotation_to_dataframe(scores: List[SectorRotationScore]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in scores])

def format_factor_scores_text(scores: List[FactorScore]) -> str:
    return "Factor Scores:\n" + "\n".join(f"- {s.factor_type.value}: {s.score} ({s.status.value})" for s in scores)

def format_factor_exposure_text(exposure: FactorExposure) -> str:
    return f"Factor Exposure [{exposure.exposure_id}]\nAggregate: {exposure.aggregate_factor_score}\nDominant: {exposure.dominant_factors}"

def format_sector_rotation_text(scores: List[SectorRotationScore]) -> str:
    return "Sector Rotation:\n" + "\n".join(f"- {s.sector}: {s.final_rotation_score} ({s.status.value})" for s in scores)

def format_theme_exposure_text(exposures: List[ThemeExposure]) -> str:
    return "Theme Exposures:\n" + "\n".join(f"- {e.theme_name}: {e.theme_score}" for e in exposures)

def format_factor_report_markdown(report: FactorReport) -> str:
    return f"# Factor Report\n\n{report.disclaimer}\n\n## Warnings\n{report.warnings}"
