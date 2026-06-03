from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUILayout, LocalUIPage, LocalUIWidget, LocalUIWidgetKind

class LocalUIFallbackRenderer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def render_plain_text_layout(self, layout: LocalUILayout) -> str:
        lines = [
            "=" * 60,
            f" BIST Signal Bot - Operator Console ({layout.name})",
            "=" * 60,
            f"Status: {layout.status.value}",
            f"Navigation: {' > '.join(layout.navigation_order)}",
            "-" * 60,
            ""
        ]

        for p in layout.pages:
            lines.append(self.render_plain_text_page(p))
            lines.append("-" * 60)

        if layout.disclaimer:
            lines.append(f"\nDisclaimer: {layout.disclaimer}")

        return "\n".join(lines)

    def render_plain_text_page(self, page: LocalUIPage) -> str:
        lines = [
            f"PAGE: {page.title.upper()} [{page.status.value}]",
            ""
        ]

        if page.warnings:
            lines.append("PAGE WARNINGS:")
            for w in page.warnings:
                lines.append(f"  ! {w}")
            lines.append("")

        for w in page.widgets:
            lines.append(self.render_plain_text_widget(w))
            lines.append("")

        return "\n".join(lines)

    def render_plain_text_widget(self, widget: LocalUIWidget) -> str:
        lines = [f"[{widget.title}] - Status: {widget.status.value}"]

        if widget.warnings:
            for w in widget.warnings:
                lines.append(f"  ! {w}")

        if widget.kind == LocalUIWidgetKind.STATUS_CARD:
            lines.append(f"  Status: {widget.content.get('status')}")
            for k, v in widget.content.get('details', {}).items():
                lines.append(f"  {k}: {v}")

        elif widget.kind == LocalUIWidgetKind.KEY_VALUE:
            for k, v in widget.content.get('items', {}).items():
                lines.append(f"  {k}: {v}")

        elif widget.kind == LocalUIWidgetKind.TABLE:
            rows = widget.content.get('rows', [])
            if not rows:
                lines.append("  (empty table)")
            else:
                headers = list(rows[0].keys())
                lines.append("  | " + " | ".join(headers) + " |")
                for r in rows:
                    vals = [str(r.get(h, "")) for h in headers]
                    lines.append("  | " + " | ".join(vals) + " |")
            if widget.content.get('truncated'):
                lines.append(f"  ... (showing {len(rows)} of {widget.content.get('total')} rows)")

        elif widget.kind == LocalUIWidgetKind.WARNING_LIST:
            for w in widget.content.get('warnings', []):
                lines.append(f"  * {w}")

        elif widget.kind == LocalUIWidgetKind.COMMAND_LIST:
            for c in widget.content.get('commands', []):
                lines.append(f"  > {c}")

        elif widget.kind in (LocalUIWidgetKind.TEXT_BLOCK, LocalUIWidgetKind.REPORT_PREVIEW):
            text = widget.content.get('text') or widget.content.get('markdown', '')
            for t_line in text.split('\n'):
                lines.append(f"  {t_line}")

        elif widget.kind == LocalUIWidgetKind.NAV_MENU:
            for item in widget.content.get('items', []):
                lines.append(f"  {item.get('title')} [{item.get('status')}]")

        else:
            lines.append(f"  (Unsupported widget kind: {widget.kind.value})")

        return "\n".join(lines)

    def fallback_message(self, reason: str) -> str:
        return f"[LOCAL UI FALLBACK] Rendering in PLAIN_TEXT mode. Reason: {reason}"
