import sys
import importlib.util
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUICapability, LocalUIBackend, LocalUIStatus

class LocalUICapabilityDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def detect_capabilities(self) -> list[LocalUICapability]:
        capabilities = []

        capabilities.append(
            LocalUICapability(
                capability_id="backend_plain_text",
                backend=LocalUIBackend.PLAIN_TEXT,
                available=True,
                status=LocalUIStatus.AVAILABLE,
                metadata={"reason": "Native support"}
            )
        )

        rich_available, rich_version = self.dependency_available("rich")
        capabilities.append(
            LocalUICapability(
                capability_id="backend_rich",
                backend=LocalUIBackend.RICH,
                available=rich_available and getattr(self.settings, "LOCAL_UI_ALLOW_RICH", True),
                dependency_name="rich",
                version=rich_version,
                status=LocalUIStatus.AVAILABLE if rich_available else LocalUIStatus.UNAVAILABLE,
                warnings=["Rich not installed"] if not rich_available else []
            )
        )

        textual_available, textual_version = self.dependency_available("textual")
        capabilities.append(
            LocalUICapability(
                capability_id="backend_textual",
                backend=LocalUIBackend.TEXTUAL,
                available=textual_available and getattr(self.settings, "LOCAL_UI_ALLOW_TEXTUAL", False),
                dependency_name="textual",
                version=textual_version,
                status=LocalUIStatus.AVAILABLE if textual_available else LocalUIStatus.UNAVAILABLE,
                warnings=["Textual not installed"] if not textual_available else []
            )
        )

        curses_available, curses_version = self.dependency_available("curses")
        capabilities.append(
            LocalUICapability(
                capability_id="backend_curses",
                backend=LocalUIBackend.CURSES,
                available=curses_available and getattr(self.settings, "LOCAL_UI_ALLOW_CURSES", False),
                dependency_name="curses",
                version=curses_version,
                status=LocalUIStatus.AVAILABLE if curses_available else LocalUIStatus.UNAVAILABLE,
                warnings=["Curses not available on this system"] if not curses_available else []
            )
        )

        return capabilities

    def detect_backend(self, backend: LocalUIBackend) -> LocalUICapability:
        caps = self.detect_capabilities()
        for cap in caps:
            if cap.backend == backend:
                return cap
        return LocalUICapability(
            capability_id=f"backend_{backend.value.lower()}",
            backend=backend,
            available=False,
            status=LocalUIStatus.UNKNOWN
        )

    def preferred_backend(self) -> LocalUIBackend:
        if not getattr(self.settings, "ENABLE_LOCAL_UI", True):
            return LocalUIBackend.PLAIN_TEXT

        backend_pref = getattr(self.settings, "LOCAL_UI_BACKEND", "AUTO")
        if backend_pref != "AUTO":
            try:
                requested = LocalUIBackend(backend_pref)
                cap = self.detect_backend(requested)
                if cap.available:
                    return requested
                elif getattr(self.settings, "LOCAL_UI_FALLBACK_TO_PLAIN_TEXT", True):
                    return LocalUIBackend.PLAIN_TEXT
            except ValueError:
                pass

        caps = {c.backend: c for c in self.detect_capabilities()}
        if caps.get(LocalUIBackend.TEXTUAL) and caps[LocalUIBackend.TEXTUAL].available:
            return LocalUIBackend.TEXTUAL
        if caps.get(LocalUIBackend.RICH) and caps[LocalUIBackend.RICH].available:
            return LocalUIBackend.RICH
        if caps.get(LocalUIBackend.CURSES) and caps[LocalUIBackend.CURSES].available:
            return LocalUIBackend.CURSES

        return LocalUIBackend.PLAIN_TEXT

    def dependency_available(self, name: str) -> tuple[bool, str | None]:
        try:
            if importlib.util.find_spec(name) is not None:
                mod = importlib.import_module(name)
                version = getattr(mod, "__version__", None)
                return True, version
            return False, None
        except ImportError:
            return False, None

    def terminal_supported(self) -> bool:
        if getattr(self.settings, "LOCAL_UI_REQUIRE_TTY", False):
            return sys.stdout.isatty()
        return True

    def fallback_backend(self) -> LocalUIBackend:
        return LocalUIBackend.PLAIN_TEXT
