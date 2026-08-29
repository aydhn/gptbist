from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from bist_signal_bot.signals.lifecycle import SignalLifecycleManager
from bist_signal_bot.signals.models import SignalAlertPolicy, SignalLifecycleState
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.signals.fingerprint import SignalFingerprintBuilder

class MockSignal:
    def __init__(self, symbol, strategy, score, direction):
        self.symbol = symbol
        self.strategy_name = strategy
        self.score = score
        self.direction = direction
        self.confidence = 50.0

def test_lifecycle_track_new(tmp_path):
    store = SignalStore(tmp_path)
    policy = SignalAlertPolicy()
    fb = SignalFingerprintBuilder()
    lm = SignalLifecycleManager(store, fb, policy)

    sig = MockSignal("ASELS", "trend", 75.0, "LONG")
    tracked, res = lm.track_signal(sig, "SCANNER")

    assert tracked.symbol == "ASELS"
    assert tracked.state == SignalLifecycleState.ACTIVE
    assert tracked.alert_count == 1
    assert res.should_send is True

def test_lifecycle_track_duplicate(tmp_path):
    store = SignalStore(tmp_path)
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0)
    fb = SignalFingerprintBuilder()
    lm = SignalLifecycleManager(store, fb, policy)

    sig1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    tracked1, res1 = lm.track_signal(sig1, "SCANNER")

    sig2 = MockSignal("ASELS", "trend", 75.4, "LONG")
    tracked2, res2 = lm.track_signal(sig2, "SCANNER")

    assert tracked2.state == SignalLifecycleState.COOLDOWN
    assert res2.should_send is False

def test_lifecycle_expire(tmp_path):
    store = SignalStore(tmp_path)
    policy = SignalAlertPolicy(validity_minutes=60)
    fb = SignalFingerprintBuilder()
    lm = SignalLifecycleManager(store, fb, policy)

    sig = MockSignal("ASELS", "trend", 75.0, "LONG")
    tracked, _ = lm.track_signal(sig, "SCANNER")

    # Backdate it
    tracked.valid_until = datetime.now(timezone.utc) - timedelta(minutes=120)
    store.update_signal(tracked)

    expired = lm.expire_stale_signals()
    assert len(expired) == 1
    assert expired[0].state == SignalLifecycleState.EXPIRED

@patch('bist_signal_bot.signals.lifecycle.logger')
@patch('bist_signal_bot.signals.lifecycle.get_settings')
def test_route_to_telegram_inbox_error_logged(mock_get_settings, mock_logger):
    mock_get_settings.return_value = MagicMock()

    manager = SignalLifecycleManager(MagicMock(), MagicMock(), MagicMock())

    settings = MagicMock()
    settings.ENABLE_TELEGRAM_CENTER = True

    eval_result = MagicMock()
    eval_result.action.value = "SEND"
    eval_result.reason = "test reason"
    eval_result.signal.symbol = "TEST"
    eval_result.signal.signal_id = "test_id"

    with patch('bist_signal_bot.app.telegram_center_app.create_notification_inbox', side_effect=ImportError("Mocked error"), create=True):
        manager.route_to_telegram_inbox(eval_result, settings)

    mock_logger.error.assert_called_once_with("Error routing to telegram inbox", exc_info=True)
