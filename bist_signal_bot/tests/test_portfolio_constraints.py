from bist_signal_bot.portfolio_research.models import ResearchPortfolioItem, PortfolioResearchRequest
from bist_signal_bot.portfolio_research.constraints import PortfolioConstraintEngine

def test_constraint_engine():
    engine = PortfolioConstraintEngine()
    req = PortfolioResearchRequest(
        max_symbol_weight=0.2,
        max_sector_weight=0.35,
        min_score=50.0
    )
    items = [
        ResearchPortfolioItem(item_id="1", symbol="A", proposed_weight=0.3, capped_weight=0.0, final_weight=0.0, score=40.0, sector="TECH", state="ACTIVE"),
        ResearchPortfolioItem(item_id="2", symbol="B", proposed_weight=0.1, capped_weight=0.0, final_weight=0.0, score=60.0, sector="TECH", state="ACTIVE"),
        ResearchPortfolioItem(item_id="3", symbol="C", proposed_weight=0.1, capped_weight=0.0, final_weight=0.0, score=70.0, sector="TECH", state="BLOCKED_BY_RISK"),
    ]

    constraints = engine.validate_items(items, req)

    # Assert
    assert items[0].state == "BLOCKED_BY_SCORE"
    assert items[2].state == "BLOCKED_BY_RISK"
    assert len(constraints) == 2

    engine.apply_weight_caps(items, req)
    assert items[0].capped_weight == 0.0 # because blocked
    assert items[1].capped_weight == 0.1
    assert items[2].capped_weight == 0.0 # because blocked
