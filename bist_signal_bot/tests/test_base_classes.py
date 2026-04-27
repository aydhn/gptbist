import pytest
from bist_signal_bot.data.base_provider import BaseDataProvider

def test_base_data_provider_instantiation():
    """Test that abstract base classes cannot be instantiated directly."""
    with pytest.raises(TypeError):
        # Should raise TypeError: Can't instantiate abstract class with abstract method
        provider = BaseDataProvider()
