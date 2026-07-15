import pytest
from bist_signal_bot.ml.leakage import MLLeakageGuard
from bist_signal_bot.core.exceptions import MLLeakageError

def test_validate_no_random_split():
    guard = MLLeakageGuard()

    # Correct case: time-based split (train comes before test)
    train_indices = [0, 1, 2, 3]
    test_indices = [4, 5, 6]
    assert guard.validate_no_random_split(train_indices, test_indices) is True

    # Leakage case: random split / overlap
    train_indices_leak = [0, 2, 4, 6]
    test_indices_leak = [1, 3, 5]
    with pytest.raises(MLLeakageError, match="Chronological overlap detected"):
        guard.validate_no_random_split(train_indices_leak, test_indices_leak)

    # Empty cases
    assert guard.validate_no_random_split([], [1, 2, 3]) is True
    assert guard.validate_no_random_split([1, 2, 3], []) is True
    assert guard.validate_no_random_split([], []) is True
