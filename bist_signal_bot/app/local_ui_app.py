from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.storage import LocalUIStore
from bist_signal_bot.local_ui.capabilities import LocalUICapabilityDetector
from bist_signal_bot.local_ui.layout import LocalUILayoutBuilder
from bist_signal_bot.local_ui.pages import LocalUIPageBuilder
from bist_signal_bot.local_ui.widgets import LocalUIWidgetBuilder
from bist_signal_bot.local_ui.navigation import LocalUINavigationController
from bist_signal_bot.local_ui.shortcuts import LocalUIShortcutRegistry
from bist_signal_bot.local_ui.runner import LocalUIRunner
from bist_signal_bot.local_ui.fallback import LocalUIFallbackRenderer
from bist_signal_bot.local_ui.status_provider import LocalUIStatusProvider
from bist_signal_bot.local_ui.safety import LocalUISafetyGuard

def create_local_ui_store(settings: Settings | None = None, base_dir=None) -> LocalUIStore:
    return LocalUIStore(settings or get_settings(), base_dir)

def create_local_ui_capability_detector(settings: Settings | None = None) -> LocalUICapabilityDetector:
    return LocalUICapabilityDetector(settings or get_settings())

def create_local_ui_layout_builder(settings: Settings | None = None, base_dir=None) -> LocalUILayoutBuilder:
    return LocalUILayoutBuilder(settings or get_settings(), base_dir)

def create_local_ui_page_builder(settings: Settings | None = None, base_dir=None) -> LocalUIPageBuilder:
    return LocalUIPageBuilder(settings or get_settings(), base_dir)

def create_local_ui_widget_builder(settings: Settings | None = None) -> LocalUIWidgetBuilder:
    return LocalUIWidgetBuilder(settings or get_settings())

def create_local_ui_navigation_controller(settings: Settings | None = None) -> LocalUINavigationController:
    return LocalUINavigationController(settings or get_settings())

def create_local_ui_shortcut_registry(settings: Settings | None = None, base_dir=None) -> LocalUIShortcutRegistry:
    return LocalUIShortcutRegistry(settings or get_settings(), base_dir)

def create_local_ui_runner(settings: Settings | None = None, base_dir=None) -> LocalUIRunner:
    return LocalUIRunner(settings or get_settings(), base_dir)

def create_local_ui_fallback_renderer(settings: Settings | None = None) -> LocalUIFallbackRenderer:
    return LocalUIFallbackRenderer(settings or get_settings())

def create_local_ui_status_provider(settings: Settings | None = None, base_dir=None) -> LocalUIStatusProvider:
    return LocalUIStatusProvider(settings or get_settings(), base_dir)

def create_local_ui_safety_guard(settings: Settings | None = None) -> LocalUISafetyGuard:
    return LocalUISafetyGuard(settings or get_settings())
