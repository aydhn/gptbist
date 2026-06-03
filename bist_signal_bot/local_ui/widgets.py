import json
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUIWidget, LocalUIWidgetKind, LocalUIStatus

class LocalUIWidgetBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _truncate(self, text: str) -> str:
        if not getattr(self.settings, "LOCAL_UI_TRUNCATE_LONG_TEXT", True):
            return text
        max_chars = getattr(self.settings, "LOCAL_UI_MAX_TEXT_CHARS", 5000)
        if len(text) > max_chars:
            return text[:max_chars] + "... [truncated]"
        return text

    def status_card(self, title: str, status: str, details: dict | None = None) -> LocalUIWidget:
        content = {"status": status, "details": details or {}}
        return LocalUIWidget(
            widget_id=f"status_card_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.STATUS_CARD,
            title=title,
            content=content,
            status=LocalUIStatus(status) if status in LocalUIStatus.__members__ else LocalUIStatus.UNKNOWN
        )

    def key_value(self, title: str, values: dict) -> LocalUIWidget:
        try:
            json.dumps(values)
        except TypeError:
            values = {"error": "Content is not JSON serializable"}

        return LocalUIWidget(
            widget_id=f"kv_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.KEY_VALUE,
            title=title,
            content={"items": values},
            status=LocalUIStatus.PASS
        )

    def table(self, title: str, rows: list[dict]) -> LocalUIWidget:
        max_rows = getattr(self.settings, "LOCAL_UI_MAX_TABLE_ROWS", 20)
        truncated_rows = rows[:max_rows]
        return LocalUIWidget(
            widget_id=f"table_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.TABLE,
            title=title,
            content={"rows": truncated_rows, "total": len(rows), "truncated": len(rows) > max_rows},
            status=LocalUIStatus.PASS
        )

    def warning_list(self, title: str, warnings: list[str]) -> LocalUIWidget:
        return LocalUIWidget(
            widget_id=f"warn_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.WARNING_LIST,
            title=title,
            content={"warnings": warnings},
            status=LocalUIStatus.WATCH if warnings else LocalUIStatus.PASS,
            warnings=warnings
        )

    def command_list(self, title: str, commands: list[str]) -> LocalUIWidget:
        return LocalUIWidget(
            widget_id=f"cmds_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.COMMAND_LIST,
            title=title,
            content={"commands": commands},
            status=LocalUIStatus.PASS
        )

    def text_block(self, title: str, text: str) -> LocalUIWidget:
        return LocalUIWidget(
            widget_id=f"text_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.TEXT_BLOCK,
            title=title,
            content={"text": self._truncate(text)},
            status=LocalUIStatus.PASS
        )

    def report_preview(self, title: str, markdown: str | None) -> LocalUIWidget:
        text = markdown or "No report content"
        return LocalUIWidget(
            widget_id=f"report_{title.lower().replace(' ', '_')}",
            kind=LocalUIWidgetKind.REPORT_PREVIEW,
            title=title,
            content={"markdown": self._truncate(text)},
            status=LocalUIStatus.PASS if markdown else LocalUIStatus.WATCH
        )

    def validate_widget(self, widget: LocalUIWidget) -> list[str]:
        errors = []
        if not widget.title:
            errors.append("Widget title cannot be empty")
        try:
            json.dumps(widget.content)
        except TypeError:
            errors.append("Widget content must be JSON serializable")
        return errors
