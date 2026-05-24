import pytest

def test_validation_architecture():
    from bist_signal_bot.validation.models import StrategyValidationRequest
    from bist_signal_bot.validation.splits import ValidationSplitBuilder
    from bist_signal_bot.validation.engine import StrategyValidationEngine
    assert StrategyValidationRequest is not None
    assert ValidationSplitBuilder is not None
    assert StrategyValidationEngine is not None
