import logging
from pathlib import Path
from datetime import datetime
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.docs.catalog import CommandCatalogBuilder
from bist_signal_bot.docs.models import DocsGenerationResult, DocsPage, DocsValidationStatus

class DocsGenerator:
    def __init__(self, catalog_builder: CommandCatalogBuilder | None = None, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.catalog_builder = catalog_builder or CommandCatalogBuilder()
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)

    def generate_all_docs(self, output_dir: Path | None = None, overwrite: bool = False) -> DocsGenerationResult:
        if not output_dir:
            output_dir = Path("docs")

        output_dir.mkdir(parents=True, exist_ok=True)
        res = DocsGenerationResult(started_at=datetime.utcnow())

        (output_dir / "01_QUICKSTART.md").write_text(self.generate_quickstart(), encoding="utf-8")
        res.pages_created += 1

        (output_dir / "03_CONFIGURATION.md").write_text(self.generate_configuration(), encoding="utf-8")
        res.pages_created += 1

        (output_dir / "04_CLI_COMMAND_CATALOG.md").write_text(self.generate_command_catalog(), encoding="utf-8")
        res.pages_created += 1

        (output_dir / "26_ARCHITECTURE.md").write_text(self.generate_architecture_doc(), encoding="utf-8")
        res.pages_created += 1

        (output_dir / "27_GLOSSARY.md").write_text(self.generate_glossary(), encoding="utf-8")
        res.pages_created += 1

        (output_dir / "28_SAFE_OPERATIONS_CHECKLIST.md").write_text(self.generate_safe_operations_checklist(), encoding="utf-8")
        res.pages_created += 1

        res.finished_at = datetime.utcnow()
        res.elapsed_seconds = (res.finished_at - res.started_at).total_seconds()
        return res

    def generate_page(self, page: DocsPage, output_dir: Path, overwrite: bool = False) -> Path:
        p = output_dir / page.path
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or overwrite:
            p.write_text(f"# {page.title}\n\n{page.description}\n", encoding="utf-8")
        return p

    def generate_quickstart(self) -> str:
        return "# Quickstart\n\nPurpose...\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_installation(self) -> str:
        return "# Installation\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_configuration(self) -> str:
        return "# Configuration\n\nTELEGRAM_BOT_TOKEN=your_telegram_bot_token_here\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_module_doc(self, module_name: str) -> str:
        return f"# {module_name}\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_architecture_doc(self) -> str:
        return "# Architecture\n\nLocal-first architecture... No real order design.\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_glossary(self) -> str:
        return "# Glossary\n\nSignalCandidate: ...\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_safe_operations_checklist(self) -> str:
        return "# Safe Operations Checklist\n\n- Security audit...\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n"

    def generate_command_catalog(self) -> str:
        cmds = self.catalog_builder.build_command_catalog()
        return f"# CLI Command Catalog\n\nBu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.\n\n" + self.catalog_builder.command_to_markdown(cmds)
