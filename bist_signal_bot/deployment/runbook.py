import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
from bist_signal_bot.deployment.models import OperatorRunbook, DeploymentProfile, FirstRunResult
from bist_signal_bot.config.settings import Settings

class OperatorRunbookBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build_runbook(self, profile: DeploymentProfile, first_run_result: Optional[FirstRunResult] = None) -> OperatorRunbook:
        sections = [
            {"title": "Kurulum Özeti", "content": "Sistem başarıyla kuruldu."},
            {"title": "Safe Profile", "content": f"Aktif profil: {profile.name}. Broker: Kapalı, Real Order: Kapalı."},
            {"title": "İlk Gün Komutları", "content": "python -m bist_signal_bot healthcheck\npython -m bist_signal_bot deploy smoke-test"},
            {"title": "Günlük Rutin", "content": "Günlük sistem kontrollerini scheduler ile yapın."},
            {"title": "Haftalık Rutin", "content": "Haftalık drift ve stress testlerini çalıştırın."},
            {"title": "Scheduler Dry-Run", "content": "Tüm scheduler jobları default dry-run çalışmaktadır."},
            {"title": "Telegram Dry-Run", "content": "Telegram bildirimleri kapalıdır/dry-run aktiftir."},
            {"title": "Backup/Maintenance", "content": "Düzenli bakım için `python -m bist_signal_bot maintenance backup-create` kullanın."},
            {"title": "Governance/Release Readiness", "content": "Governance policy'leri uygulayın."},
            {"title": "Sorun Giderme", "content": "Logları inceleyin veya `deploy doctor` çalıştırın."},
            {"title": "Yasaklı Davranışlar", "content": "HTML scraping, ücretli API kullanımı yasaktır."},
            {"title": "No Real Order Reminder", "content": "Bu araç yatırım tavsiyesi vermez ve gerçek emir göndermez."},
        ]

        return OperatorRunbook(
            runbook_id=str(uuid.uuid4()),
            profile_type=profile.profile_type,
            created_at=datetime.now(UTC),
            title=f"Operator Runbook - {profile.name}",
            sections=sections,
            commands=[["python", "-m", "bist_signal_bot", "healthcheck"]]
        )

    def render_markdown(self, runbook: OperatorRunbook) -> str:
        lines = [f"# {runbook.title}", f"**Oluşturulma:** {runbook.created_at}", "", f"_{runbook.disclaimer}_", ""]
        for section in runbook.sections:
            lines.append(f"## {section['title']}")
            lines.append(section['content'])
            lines.append("")
        return "\n".join(lines)

    def write_runbook(self, runbook: OperatorRunbook, output_dir: Path) -> Path:
        md = self.render_markdown(runbook)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"runbook_{runbook.runbook_id}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md)
        return file_path
