from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUIPage, LocalUIPageKind, LocalUIStatus
from bist_signal_bot.local_ui.widgets import LocalUIWidgetBuilder

class LocalUIPageBuilder:
    def __init__(self, settings: Settings | None = None, base_dir=None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self.widget_builder = LocalUIWidgetBuilder(self.settings)

    def build_page(self, page_kind: LocalUIPageKind) -> LocalUIPage:
        if page_kind == LocalUIPageKind.HOME:
            return self.build_home_page()
        elif page_kind == LocalUIPageKind.HEALTHCHECK:
            return self.build_healthcheck_page()
        elif page_kind == LocalUIPageKind.DOCTOR:
            return self.build_doctor_page()
        elif page_kind == LocalUIPageKind.QA:
            return self.build_qa_page()
        elif page_kind == LocalUIPageKind.OPS:
            return self.build_ops_page()
        elif page_kind == LocalUIPageKind.REPORTS:
            return self.build_reports_page()
        elif page_kind == LocalUIPageKind.ORCHESTRATOR:
            return self.build_orchestrator_page()
        elif page_kind == LocalUIPageKind.COMMANDS:
            return self.build_commands_page()
        elif page_kind == LocalUIPageKind.HELP:
            return self.build_help_page()
        else:
            return self.build_module_page(page_kind, page_kind.value.lower())

    def build_home_page(self) -> LocalUIPage:
        widgets = [
            self.widget_builder.status_card("System Status", "PASS", {"uptime": "1h", "mode": "RESEARCH"}),
            self.widget_builder.text_block("Welcome", "BIST Signal Bot Operator Console.")
        ]
        return LocalUIPage(
            page_id=LocalUIPageKind.HOME.value,
            page_kind=LocalUIPageKind.HOME,
            title="Home",
            widgets=widgets,
            status=LocalUIStatus.PASS
        )

    def build_healthcheck_page(self) -> LocalUIPage:
        widgets = [
            self.widget_builder.status_card("Health", "WATCH", {"details": "Some stores missing"})
        ]
        return LocalUIPage(
            page_id=LocalUIPageKind.HEALTHCHECK.value,
            page_kind=LocalUIPageKind.HEALTHCHECK,
            title="Healthcheck",
            widgets=widgets,
            status=LocalUIStatus.WATCH
        )

    def build_doctor_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.DOCTOR.value,
            page_kind=LocalUIPageKind.DOCTOR,
            title="Doctor",
            widgets=[self.widget_builder.status_card("Doctor Status", "WATCH")],
            status=LocalUIStatus.WATCH
        )

    def build_qa_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.QA.value,
            page_kind=LocalUIPageKind.QA,
            title="QA Gate",
            widgets=[self.widget_builder.status_card("QA Status", "WATCH")],
            status=LocalUIStatus.WATCH
        )

    def build_ops_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.OPS.value,
            page_kind=LocalUIPageKind.OPS,
            title="Ops Readiness",
            widgets=[self.widget_builder.status_card("Ops Status", "WATCH")],
            status=LocalUIStatus.WATCH
        )

    def build_reports_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.REPORTS.value,
            page_kind=LocalUIPageKind.REPORTS,
            title="Reports",
            widgets=[self.widget_builder.text_block("Reports", "No recent reports found.")],
            status=LocalUIStatus.WATCH
        )

    def build_orchestrator_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.ORCHESTRATOR.value,
            page_kind=LocalUIPageKind.ORCHESTRATOR,
            title="Orchestrator",
            widgets=[self.widget_builder.status_card("Orchestrator", "WATCH")],
            status=LocalUIStatus.WATCH
        )

    def build_module_page(self, page_kind: LocalUIPageKind, module_name: str) -> LocalUIPage:
        return LocalUIPage(
            page_id=page_kind.value,
            page_kind=page_kind,
            title=module_name.replace("_", " ").title(),
            widgets=[self.widget_builder.status_card(f"{module_name} Status", "WATCH")],
            status=LocalUIStatus.WATCH
        )

    def build_commands_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.COMMANDS.value,
            page_kind=LocalUIPageKind.COMMANDS,
            title="Commands",
            widgets=[self.widget_builder.command_list("Shortcuts", ["local-ui status", "local-ui preview --page HOME"])],
            status=LocalUIStatus.PASS
        )

    def build_help_page(self) -> LocalUIPage:
        return LocalUIPage(
            page_id=LocalUIPageKind.HELP.value,
            page_kind=LocalUIPageKind.HELP,
            title="Help",
            widgets=[self.widget_builder.text_block("Help", "Navigate using terminal. Destructive actions are blocked.")],
            status=LocalUIStatus.PASS
        )
