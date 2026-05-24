import pytest
from bist_signal_bot.execution_sim.quality import ExecutionQualityAnalyzer
from bist_signal_bot.execution_sim.models import SimulatedFill, SimulatedFillStatus

class MockFill:
    def __init__(self, status):
        self.status = status
        self.cost_breakdown = None
        self.slippage_estimate = None

def test_execution_quality_analyzer_fill_rate():
    analyzer = ExecutionQualityAnalyzer()
    fills = [MockFill(SimulatedFillStatus.FILLED), MockFill(SimulatedFillStatus.NOT_FILLED)]
    assert analyzer.fill_rate(fills) == 50.0

def test_execution_quality_analyzer_empty():
    analyzer = ExecutionQualityAnalyzer()
    report = analyzer.analyze_fills([])
    assert report.total_orders == 0
