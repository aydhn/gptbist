import pytest

def test_portfolio_research_liquidity_penalty():
    from bist_signal_bot.portfolio_research.models import ScoredAsset
    asset = ScoredAsset(symbol="ASELS", final_score=100.0, liquidity_capacity_score=50.0, execution_penalty=10.0)
    assert asset.execution_penalty == 10.0
