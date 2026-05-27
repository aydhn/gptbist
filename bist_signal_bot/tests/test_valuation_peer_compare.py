from datetime import datetime, timezone
from bist_signal_bot.valuation.peer_compare import PeerValuationComparator
from bist_signal_bot.valuation.models import ValuationMetricType

def test_peer_discount_premium():
    comp = PeerValuationComparator()
    # If I am 10, peer median is 20, discount is -50%
    assert comp.relative_discount_premium(10.0, 20.0) == -50.0
    # If I am 30, peer median is 20, premium is +50%
    assert comp.relative_discount_premium(30.0, 20.0) == 50.0

def test_peer_classification():
    comp = PeerValuationComparator()
    assert comp.classify_relative(5.0, -20.0).value == "EXTREME_CHEAP"
    assert comp.classify_relative(20.0, -10.0).value == "CHEAP"
    assert comp.classify_relative(80.0, 10.0).value == "EXPENSIVE"
    assert comp.classify_relative(95.0, 20.0).value == "EXTREME_EXPENSIVE"
