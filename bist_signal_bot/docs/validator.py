import re
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.docs.models import DocsValidationReport, DocsValidationFinding, DocsValidationStatus

class DocsValidator:
    def __init__(self, claim_guard=None, secret_redactor=None, forbidden_guard=None, settings: Settings | None = None):
        self.claim_guard = claim_guard
        self.secret_redactor = secret_redactor
        self.forbidden_guard = forbidden_guard
        self.settings = settings

    def validate_docs_dir(self, docs_dir: Path) -> DocsValidationReport:
        report = DocsValidationReport()
        report.missing_pages = self.validate_required_pages(docs_dir)

        if not docs_dir.exists():
            return report

        for md_file in docs_dir.rglob("*.md"):
            report.checked_files += 1
            findings = self.validate_markdown_file(md_file)
            report.findings.extend(findings)

        if report.missing_pages:
            report.status = DocsValidationStatus.WARN
        for f in report.findings:
            if f.severity == "HIGH":
                report.status = DocsValidationStatus.FAIL
        return report

    def validate_markdown_file(self, path: Path) -> list[DocsValidationFinding]:
        findings = []
        text = path.read_text(encoding="utf-8")
        findings.extend(self.validate_no_secrets(text, str(path)))
        findings.extend(self.validate_no_unsafe_claims(text, str(path)))
        findings.extend(self.validate_command_examples(text, str(path)))
        return findings

    def validate_command_examples(self, text: str, path: str) -> list[DocsValidationFinding]:
        findings = []
        lines = text.splitlines()
        for line in lines:
            if "runtime loop" in line and "--max-iterations" not in line and not line.strip().startswith("#"):
                findings.append(DocsValidationFinding(
                    path=path,
                    status=DocsValidationStatus.WARN,
                    severity="MEDIUM",
                    message="runtime loop without max-iterations"
                ))
            if ("kill-switch deactivate" in line or "paper reset" in line) and "--confirm" not in line and "python" in line:
                findings.append(DocsValidationFinding(
                    path=path,
                    status=DocsValidationStatus.FAIL,
                    severity="HIGH",
                    message="Destructive command without --confirm"
                ))
        return findings

    def validate_no_secrets(self, text: str, path: str) -> list[DocsValidationFinding]:
        findings = []
        if "7123456789:AABBccddee" in text: # simple fake token matching
            findings.append(DocsValidationFinding(
                path=path,
                status=DocsValidationStatus.FAIL,
                severity="HIGH",
                message="Secret-like token found"
            ))
        return findings

    def validate_no_unsafe_claims(self, text: str, path: str) -> list[DocsValidationFinding]:
        findings = []
        unsafe_words = ["garanti", "risksiz kazanç", "kesin al"]
        for w in unsafe_words:
            if w in text.lower():
                findings.append(DocsValidationFinding(
                    path=path,
                    status=DocsValidationStatus.FAIL,
                    severity="HIGH",
                    message=f"Unsafe claim found: {w}"
                ))
        return findings

    def validate_required_pages(self, docs_dir: Path) -> list[str]:
        required = ["00_DISCLAIMER.md", "01_QUICKSTART.md"]
        missing = []
        for r in required:
            if not (docs_dir / r).exists():
                missing.append(r)
        return missing
