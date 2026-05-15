from pathlib import Path
from bist_signal_bot.docs.models import Runbook, RunbookStep

class RunbookBuilder:
    def build_runtime_stuck_lock_runbook(self) -> Runbook:
        return Runbook(
            runbook_id="RB-001",
            title="Runtime Stuck Lock Recovery",
            symptom="Runtime orchestrator fails to start due to existing lock.",
            severity="HIGH",
            steps=[
                RunbookStep(step_number=1, title="Check monitor diagnostics", expected_result="Diagnostics show lock issue"),
                RunbookStep(step_number=2, title="Unlock stale", command="python -m bist_signal_bot runtime unlock --stale-only", expected_result="Stale lock removed")
            ]
        )

    def build_telegram_failure_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-002", title="Telegram Failure", symptom="Telegram fails", severity="MEDIUM")

    def build_data_stale_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-003", title="Data Stale", symptom="Data stale", severity="MEDIUM")

    def build_paper_ledger_issue_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-004", title="Paper Ledger Issue", symptom="Ledger corrupted", severity="MEDIUM")

    def build_ml_model_missing_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-005", title="ML Model Missing", symptom="Model missing", severity="MEDIUM")

    def build_kill_switch_active_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-006", title="Kill-Switch Active", symptom="Kill-switch active", severity="HIGH")

    def build_quality_gate_failed_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-007", title="Quality Gate Failed", symptom="Quality fail", severity="MEDIUM")

    def build_security_preflight_failed_runbook(self) -> Runbook:
        return Runbook(runbook_id="RB-008", title="Security Preflight Failed", symptom="Preflight fail", severity="HIGH")

    def render_runbook_markdown(self, runbook: Runbook) -> str:
        md = f"# {runbook.title}\n\n**Symptom:** {runbook.symptom}\n\n**Severity:** {runbook.severity}\n\n"
        md += "## Steps\n"
        for s in runbook.steps:
            md += f"{s.step_number}. {s.title}\n"
        md += f"\n{runbook.disclaimer}\n"
        return md

    def generate_all_runbooks(self, output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        rbs = [
            self.build_runtime_stuck_lock_runbook(),
            self.build_telegram_failure_runbook(),
            self.build_data_stale_runbook(),
            self.build_paper_ledger_issue_runbook(),
            self.build_ml_model_missing_runbook(),
            self.build_kill_switch_active_runbook(),
            self.build_quality_gate_failed_runbook(),
            self.build_security_preflight_failed_runbook()
        ]

        paths = {}
        for rb in rbs:
            p = output_dir / f"{rb.runbook_id}.md"
            p.write_text(self.render_runbook_markdown(rb), encoding="utf-8")
            paths[rb.runbook_id] = p
        return paths
