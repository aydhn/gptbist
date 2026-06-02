import pytest
from datetime import datetime, timezone
from bist_signal_bot.local_ui.models import (
    LocalUIStatus, LocalUIBackend, LocalUIPageKind, LocalUIWidgetKind, LocalUIActionKind,
    LocalUICapability, LocalUIWidget, LocalUIPage, LocalUILayout, LocalUIShortcut,
    LocalUIRunResult, LocalUIReport
)

def test_capability_model():
    cap = LocalUICapability(
        capability_id="test",
        backend=LocalUIBackend.PLAIN_TEXT,
        available=True
    )
    assert cap.backend == LocalUIBackend.PLAIN_TEXT
    assert cap.available is True
    assert cap.status == LocalUIStatus.UNKNOWN

def test_widget_model_json_serializable():
    w = LocalUIWidget(
        widget_id="w1",
        kind=LocalUIWidgetKind.TEXT_BLOCK,
        title="Title",
        content={"key": "value"}
    )
    assert w.content == {"key": "value"}

def test_page_model_disclaimer():
    page = LocalUIPage(
        page_id="p1",
        page_kind=LocalUIPageKind.HOME,
        title="Home"
    )
    assert "not investment advice" in page.disclaimer.lower()

def test_shortcut_model_disclaimer():
    shortcut = LocalUIShortcut(
        shortcut_id="s1",
        label="Test",
        command="test",
        action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
        dry_run=True,
        requires_confirm=False,
        allowed_in_tui=True,
        audience="Operator"
    )
    assert "not investment advice" in shortcut.disclaimer.lower()

def test_run_result_model():
    result = LocalUIRunResult(
        run_id="run1",
        backend=LocalUIBackend.PLAIN_TEXT,
        started_at=datetime.now(timezone.utc)
    )
    assert result.status == LocalUIStatus.UNKNOWN
