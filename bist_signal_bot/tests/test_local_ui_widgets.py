import pytest
from bist_signal_bot.local_ui.widgets import LocalUIWidgetBuilder
from bist_signal_bot.local_ui.models import LocalUIWidgetKind, LocalUIStatus

class MockSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __getattr__(self, name):
        return None

def test_status_card_widget():
    builder = LocalUIWidgetBuilder(MockSettings())
    widget = builder.status_card("Test", "PASS")
    assert widget.kind == LocalUIWidgetKind.STATUS_CARD
    assert widget.status == LocalUIStatus.PASS
    assert widget.content["status"] == "PASS"

def test_long_text_truncate():
    settings = MockSettings(LOCAL_UI_TRUNCATE_LONG_TEXT=True, LOCAL_UI_MAX_TEXT_CHARS=10)
    builder = LocalUIWidgetBuilder(settings)
    widget = builder.text_block("Title", "This is a very long text that should be truncated")
    assert "[truncated]" in widget.content["text"]
    assert len(widget.content["text"]) < 40

def test_widget_validation_json_serializable():
    builder = LocalUIWidgetBuilder(MockSettings())
    class NonSerializable:
        pass

    widget = builder.key_value("Title", {"key": NonSerializable()})
    errors = builder.validate_widget(widget)
    assert not errors
    assert "error" in widget.content["items"]

def test_table_widget_truncate():
    settings = MockSettings(LOCAL_UI_MAX_TABLE_ROWS=2)
    builder = LocalUIWidgetBuilder(settings)
    rows = [{"a": 1}, {"a": 2}, {"a": 3}]
    widget = builder.table("Title", rows)
    assert len(widget.content["rows"]) == 2
    assert widget.content["truncated"] is True
