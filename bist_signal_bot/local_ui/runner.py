import uuid
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import (
    LocalUIRunResult, LocalUILayout, LocalUIPage,
    LocalUIShortcut, LocalUIBackend, LocalUIStatus, LocalUIActionKind
)
from bist_signal_bot.local_ui.layout import LocalUILayoutBuilder
from bist_signal_bot.local_ui.fallback import LocalUIFallbackRenderer
from bist_signal_bot.local_ui.capabilities import LocalUICapabilityDetector
from bist_signal_bot.local_ui.safety import LocalUISafetyGuard

class LocalUIRunner:
    def __init__(self, settings: Settings | None = None, base_dir=None):
        self.settings = settings or get_settings()
        self.layout_builder = LocalUILayoutBuilder(self.settings, base_dir)
        self.fallback = LocalUIFallbackRenderer(self.settings)
        self.detector = LocalUICapabilityDetector(self.settings)
        self.safety = LocalUISafetyGuard(self.settings)

    def should_use_fallback(self, backend: LocalUIBackend | None = None) -> bool:
        if backend == LocalUIBackend.PLAIN_TEXT:
            return True
        if not self.detector.terminal_supported():
            return True

        pref = backend or self.detector.preferred_backend()
        if pref == LocalUIBackend.PLAIN_TEXT:
            return True

        cap = self.detector.detect_backend(pref)
        return not cap.available

    def launch(self, backend: LocalUIBackend | None = None, page: str | None = None, dry_run: bool = True) -> LocalUIRunResult:
        layout = self.layout_builder.build_layout(backend)
        return self.render_layout(layout, backend)

    def render_layout(self, layout: LocalUILayout, backend: LocalUIBackend | None = None) -> LocalUIRunResult:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        use_fallback = self.should_use_fallback(backend or layout.backend)
        actual_backend = LocalUIBackend.PLAIN_TEXT if use_fallback else (backend or layout.backend)

        warnings = []
        errors = []
        rendered = []

        safe_findings = self.safety.validate_layout(layout)
        if any("Unsafe command" in f for f in safe_findings):
            errors.extend(safe_findings)
            status = LocalUIStatus.BLOCKED
        else:
            warnings.extend(safe_findings)

            if use_fallback:
                try:
                    text = self.fallback.render_plain_text_layout(layout)
                    print(text)
                    rendered = [p.page_id for p in layout.pages]
                    status = LocalUIStatus.PASS
                except Exception as e:
                    errors.append(f"Fallback rendering failed: {e}")
                    status = LocalUIStatus.FAIL
            else:
                print(f"[MOCK TUI RENDER: {actual_backend.value}]")
                rendered = [p.page_id for p in layout.pages]
                status = LocalUIStatus.PASS

        return LocalUIRunResult(
            run_id=run_id,
            backend=actual_backend,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status=status,
            rendered_pages=rendered,
            warnings=warnings,
            errors=errors
        )

    def render_page(self, page: LocalUIPage, backend: LocalUIBackend | None = None) -> str:
        if self.should_use_fallback(backend):
            return self.fallback.render_plain_text_page(page)
        return f"[MOCK TUI RENDER PAGE: {page.page_id}]"

    def run_shortcut(self, shortcut: LocalUIShortcut, dry_run: bool = True) -> dict:
        result = {
            "shortcut_id": shortcut.shortcut_id,
            "status": "BLOCKED",
            "message": "",
            "dry_run": dry_run
        }

        findings = self.safety.validate_shortcuts([shortcut])
        if findings and any("Unsafe" in f for f in findings):
            result["message"] = f"Shortcut safety check failed: {findings}"
            return result

        if not shortcut.allowed_in_tui:
            result["message"] = "Shortcut not allowed in TUI"
            return result

        if not dry_run and shortcut.requires_confirm:
            result["message"] = "Write actions require explicit confirm, which TUI blocks by default"
            return result

        result["status"] = "SUCCESS"
        result["message"] = f"Executed: {shortcut.command}"
        return result
