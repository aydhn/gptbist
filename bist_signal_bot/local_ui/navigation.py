from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUILayout, LocalUIPage, LocalUIWidget, LocalUIWidgetKind, LocalUIStatus

class LocalUINavigationController:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def next_page(self, layout: LocalUILayout, current_page_id: str) -> LocalUIPage | None:
        if not layout.navigation_order:
            return None
        try:
            idx = layout.navigation_order.index(current_page_id)
            if idx < len(layout.navigation_order) - 1:
                next_id = layout.navigation_order[idx + 1]
                return self.get_page(layout, next_id)
            return None
        except ValueError:
            return None

    def previous_page(self, layout: LocalUILayout, current_page_id: str) -> LocalUIPage | None:
        if not layout.navigation_order:
            return None
        try:
            idx = layout.navigation_order.index(current_page_id)
            if idx > 0:
                prev_id = layout.navigation_order[idx - 1]
                return self.get_page(layout, prev_id)
            return None
        except ValueError:
            return None

    def get_page(self, layout: LocalUILayout, page_id_or_kind: str) -> LocalUIPage | None:
        for p in layout.pages:
            if p.page_id == page_id_or_kind or p.page_kind.value == page_id_or_kind:
                return p
        return None

    def nav_menu(self, layout: LocalUILayout) -> LocalUIWidget:
        menu_items = []
        for pid in layout.navigation_order:
            page = self.get_page(layout, pid)
            if page:
                menu_items.append({"id": pid, "title": page.title, "status": page.status.value})

        return LocalUIWidget(
            widget_id="main_nav_menu",
            kind=LocalUIWidgetKind.NAV_MENU,
            title="Navigation",
            content={"items": menu_items},
            status=LocalUIStatus.PASS
        )

    def validate_navigation(self, layout: LocalUILayout) -> list[str]:
        errors = []
        for nav_id in layout.navigation_order:
            if not self.get_page(layout, nav_id):
                errors.append(f"Page ID {nav_id} in navigation order but not found in layout pages")
        return errors
