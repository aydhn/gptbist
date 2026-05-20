from bist_signal_bot.portfolio_research.models import ResearchPortfolioItem, PortfolioResearchRequest, AllocationMethod

def test_research_portfolio_item_validation():
    item = ResearchPortfolioItem(
        item_id="123",
        symbol=" asels ",
        proposed_weight=1.5,
        capped_weight=-0.5,
        final_weight=0.5,
        score=150.0
    )
    assert item.symbol == "ASELS"
    assert item.proposed_weight == 1.0
    assert item.capped_weight == 0.0
    assert item.final_weight == 0.5
    assert item.score == 100.0

def test_portfolio_research_request_validation():
    req = PortfolioResearchRequest(
        max_items=-5,
        max_symbol_weight=1.5,
        min_score=150.0
    )
    assert req.max_items == 10
    assert req.max_symbol_weight == 1.0
    assert req.min_score == 100.0
