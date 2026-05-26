import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.constraints import PortfolioConstraintEngine
from bist_signal_bot.portfolio_construction.models import PortfolioPositionResearch, PortfolioConstraint, ConstraintType, ConstraintSeverity

def test_constraint_engine_violations():
    settings = Settings()
    settings.PORTFOLIO_MAX_SYMBOL_WEIGHT = 0.20
    settings.PORTFOLIO_MAX_SECTOR_WEIGHT = 0.35
    engine = PortfolioConstraintEngine(settings)

    p1 = PortfolioPositionResearch(position_id="1", symbol="ASELS", sector="TECH", current_weight=0.0, target_weight=0.30, weight_delta=0.30)
    p2 = PortfolioPositionResearch(position_id="2", symbol="LOGO", sector="TECH", current_weight=0.0, target_weight=0.10, weight_delta=0.10)

    c_sym = PortfolioConstraint(constraint_id="1", constraint_type=ConstraintType.MAX_SYMBOL_WEIGHT, name="sym", limit_value=0.20, severity=ConstraintSeverity.HIGH)
    c_sec = PortfolioConstraint(constraint_id="2", constraint_type=ConstraintType.MAX_SECTOR_WEIGHT, name="sec", limit_value=0.35, severity=ConstraintSeverity.MEDIUM)

    v_sym = engine.check_max_symbol_weight([p1, p2], c_sym)
    assert len(v_sym) == 1
    assert v_sym[0].symbol == "ASELS"

    v_sec = engine.check_max_sector_weight([p1, p2], c_sec)
    assert len(v_sec) == 1
    assert v_sec[0].sector == "TECH"
