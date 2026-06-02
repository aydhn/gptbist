from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import (
    LocalUILayout, LocalUIPage, LocalUIPageKind, LocalUIBackend, LocalUIStatus
)
from bist_signal_bot.local_ui.capabilities import LocalUICapabilityDetector
from bist_signal_bot.local_ui.pages import LocalUIPageBuilder

class LocalUILayoutBuilder:
    def __init__(self, settings: Settings | None = None, base_dir=None):
        self.settings = settings or get_settings()
        self.page_builder = LocalUIPageBuilder(self.settings, base_dir)

    def build_layout(self, backend: LocalUIBackend | None = None) -> LocalUILayout:
        if backend is None:
            detector = LocalUICapabilityDetector(self.settings)
            backend = detector.preferred_backend()

        pages = self.default_pages()
        nav_order = self.navigation_order(pages)

        status = LocalUIStatus.PASS
        warnings = []

        page_ids = {p.page_id for p in pages}
        missing_in_nav = page_ids - set(nav_order)
        if missing_in_nav:
            warnings.append(f"Pages missing from navigation: {missing_in_nav}")
            status = LocalUIStatus.WATCH

        return LocalUILayout(
            layout_id="default_layout",
            name="Main Local Console",
            backend=backend,
            pages=pages,
            navigation_order=nav_order,
            default_page="HOME",
            status=status,
            warnings=warnings
        )

    def default_pages(self) -> list[LocalUIPage]:
        kinds = [
            LocalUIPageKind.HOME,
            LocalUIPageKind.HEALTHCHECK,
            LocalUIPageKind.DOCTOR,
            LocalUIPageKind.QA,
            LocalUIPageKind.OPS,
            LocalUIPageKind.REPORTS,
            LocalUIPageKind.ORCHESTRATOR,
            LocalUIPageKind.DATA_CATALOG,
            LocalUIPageKind.FEATURE_STORE,
            LocalUIPageKind.MODEL_REGISTRY,
            LocalUIPageKind.MONITORING,
            LocalUIPageKind.LEADERBOARD,
            LocalUIPageKind.FINAL_AUDIT,
            LocalUIPageKind.FINAL_HANDOFF,
            LocalUIPageKind.PERFORMANCE,
            LocalUIPageKind.DATA_IMPORT,
            LocalUIPageKind.SYNTHETIC_SCENARIOS,
            LocalUIPageKind.REPORT_TEMPLATES,
            LocalUIPageKind.COMMANDS,
            LocalUIPageKind.HELP
        ]
        pages = []
        for kind in kinds:
            pages.append(self.page_builder.build_page(kind))
        return pages

    def navigation_order(self, pages: list[LocalUIPage]) -> list[str]:
        return [p.page_id for p in pages]

    def validate_layout(self, layout: LocalUILayout) -> list[str]:
        errors = []
        if not layout.pages:
            errors.append("Layout has no pages")
        if not layout.navigation_order:
            errors.append("Layout has empty navigation order")

        page_ids = {p.page_id for p in layout.pages}
        for nav_id in layout.navigation_order:
            if nav_id not in page_ids:
                errors.append(f"Navigation order contains unknown page id: {nav_id}")

        if layout.default_page not in page_ids:
            errors.append(f"Default page {layout.default_page} not found in pages")

        return errors

    def layout_summary(self, layout: LocalUILayout) -> dict:
        return {
            "layout_id": layout.layout_id,
            "name": layout.name,
            "backend": layout.backend.value,
            "page_count": len(layout.pages),
            "status": layout.status.value,
            "warnings_count": len(layout.warnings)
        }
