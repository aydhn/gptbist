from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUIShortcut, LocalUIActionKind, LocalUIPageKind

class LocalUIShortcutRegistry:
    def __init__(self, settings: Settings | None = None, base_dir=None):
        self.settings = settings or get_settings()

    def default_shortcuts(self) -> list[LocalUIShortcut]:
        return [
            LocalUIShortcut(
                shortcut_id="healthcheck_all",
                label="Run System Healthcheck",
                command="healthcheck --bootstrap --ops",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Operator"
            ),
            LocalUIShortcut(
                shortcut_id="doctor_ops",
                label="Run Ops Doctor",
                command="doctor --ops",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Operator"
            ),
            LocalUIShortcut(
                shortcut_id="qa_release_gate",
                label="Run QA Release Gate",
                command="qa release-gate --include-final-audit",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="QA/Operator"
            ),
            LocalUIShortcut(
                shortcut_id="ops_readiness",
                label="Check Ops Readiness",
                command="ops readiness --include-final-audit",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Operator"
            ),
            LocalUIShortcut(
                shortcut_id="reports_daily_dry",
                label="Generate Daily Report (Dry Run)",
                command="reports daily --dry-run",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Analyst"
            ),
            LocalUIShortcut(
                shortcut_id="orchestrator_quick_scan",
                label="Orchestrator Quick Scan (Dry Run)",
                command="orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Researcher"
            ),
            LocalUIShortcut(
                shortcut_id="perf_benchmark",
                label="Performance Benchmark",
                command="performance benchmark --scenario ORCHESTRATOR_DRY_RUN",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Developer"
            ),
            LocalUIShortcut(
                shortcut_id="synth_validate",
                label="Validate Synthetic Scenarios",
                command="synthetic-scenarios validate --scenario full_pipeline_demo_v1",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="QA"
            ),
            LocalUIShortcut(
                shortcut_id="final_audit_go",
                label="Final Audit Go/No-Go",
                command="final-audit go-no-go",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Release Manager"
            ),
            LocalUIShortcut(
                shortcut_id="final_handoff_show",
                label="Show Latest Final Handoff",
                command="final-handoff show --latest",
                action_kind=LocalUIActionKind.DRY_RUN_COMMAND,
                dry_run=True,
                requires_confirm=False,
                allowed_in_tui=True,
                audience="Operator"
            )
        ]

    def shortcuts_for_page(self, page_kind: LocalUIPageKind) -> list[LocalUIShortcut]:
        all_shortcuts = self.default_shortcuts()
        mapping = {
            LocalUIPageKind.HEALTHCHECK: ["healthcheck_all"],
            LocalUIPageKind.DOCTOR: ["doctor_ops"],
            LocalUIPageKind.QA: ["qa_release_gate"],
            LocalUIPageKind.OPS: ["ops_readiness"],
            LocalUIPageKind.REPORTS: ["reports_daily_dry"],
            LocalUIPageKind.ORCHESTRATOR: ["orchestrator_quick_scan"],
            LocalUIPageKind.PERFORMANCE: ["perf_benchmark"],
            LocalUIPageKind.SYNTHETIC_SCENARIOS: ["synth_validate"],
            LocalUIPageKind.FINAL_AUDIT: ["final_audit_go"],
            LocalUIPageKind.FINAL_HANDOFF: ["final_handoff_show"]
        }

        ids = mapping.get(page_kind, [])
        return [s for s in all_shortcuts if s.shortcut_id in ids]

    def validate_shortcut(self, shortcut: LocalUIShortcut) -> list[str]:
        errors = []
        if getattr(self.settings, "LOCAL_UI_BLOCK_WRITE_ACTIONS", True) and not shortcut.requires_confirm and not shortcut.dry_run:
            errors.append("Destructive commands must be dry-run or require confirm")

        cmd_lower = shortcut.command.lower()
        blocked_terms = ["live", "broker", "market order", "buy order", "sell order", "kesin al", "kesin sat", "işlem yapılabilir", "hedef fiyat"]
        if getattr(self.settings, "LOCAL_UI_BLOCK_ORDER_TERMS", True) or getattr(self.settings, "LOCAL_UI_BLOCK_BROKER_TERMS", True):
            for term in blocked_terms:
                if term in cmd_lower:
                    errors.append(f"Command contains blocked term: {term}")

        return errors

    def safe_shortcut_summary(self, shortcut: LocalUIShortcut) -> dict:
        return {
            "shortcut_id": shortcut.shortcut_id,
            "label": shortcut.label,
            "command": shortcut.command,
            "dry_run": shortcut.dry_run,
            "requires_confirm": shortcut.requires_confirm,
            "allowed_in_tui": shortcut.allowed_in_tui
        }

    def blocked_shortcuts(self) -> list[LocalUIShortcut]:
        return [
            LocalUIShortcut(
                shortcut_id="blocked_trade",
                label="Execute Trade",
                command="execute --live",
                action_kind=LocalUIActionKind.BLOCKED_WRITE_ACTION,
                dry_run=False,
                requires_confirm=False,
                allowed_in_tui=False,
                audience="Operator"
            )
        ]
