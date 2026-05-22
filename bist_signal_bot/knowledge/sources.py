import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.models import KnowledgeDocument, KnowledgeSourceType, KnowledgeDocumentStatus
from bist_signal_bot.storage.paths import get_data_dir


class KnowledgeSourceCollector:

    def __init__(self, settings: Settings | None = None):
        self.settings = settings
        self.data_dir = get_data_dir(settings) if settings else Path("data")

    def collect_documents(self, source_types: list[KnowledgeSourceType] | None = None, include_archived: bool = False) -> list[KnowledgeDocument]:
        docs = []
        types_to_collect = source_types or list(KnowledgeSourceType)

        if KnowledgeSourceType.RESEARCH_LEDGER in types_to_collect:
            docs.extend(self.collect_from_research_ledger())

        if KnowledgeSourceType.REVIEW_THESIS in types_to_collect:
            docs.extend(self.collect_from_review_thesis())

        if KnowledgeSourceType.DECISION_JOURNAL in types_to_collect:
            docs.extend(self.collect_from_decision_journal())

        # Collect others with empty stubs for now to prevent breaking,
        # actual parsing would map to corresponding data sources (reports, backtests, etc.)

        if not include_archived:
            docs = [d for d in docs if d.status == KnowledgeDocumentStatus.ACTIVE]

        return docs

    def collect_from_research_ledger(self) -> list[KnowledgeDocument]:
        ledger_file = self.data_dir / "research" / "ledger.jsonl"
        if not ledger_file.exists():
            return []

        docs = []
        try:
            with ledger_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        record = json.loads(line)
                        if "payload" not in record or "record_id" not in record:
                            continue

                        record_id = record["record_id"]
                        event_type = record.get("event_type", "UNKNOWN")
                        payload = record["payload"]

                        symbol = payload.get("symbol")
                        strategy = payload.get("strategy_name")

                        text = f"Research Ledger Event: {event_type}\n"
                        text += json.dumps(payload, indent=2, ensure_ascii=False)

                        docs.append(
                            KnowledgeDocument(
                                document_id=f"ledger_{record_id}",
                                source_type=KnowledgeSourceType.RESEARCH_LEDGER,
                                source_ref=record_id,
                                symbol=symbol,
                                strategy_name=strategy,
                                title=f"Ledger {event_type} - {symbol or 'System'}",
                                text=text,
                                created_at=datetime.fromisoformat(record.get("created_at", datetime.now().isoformat())),
                                updated_at=datetime.fromisoformat(record.get("created_at", datetime.now().isoformat()))
                            )
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        return docs

    def collect_from_signal_lifecycle(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_review_inbox(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_decision_journal(self) -> list[KnowledgeDocument]:
        journal_file = self.data_dir / "review" / "decision_journal.jsonl"
        if not journal_file.exists():
            return []

        docs = []
        try:
            with journal_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        record = json.loads(line)
                        entry_id = record.get("entry_id", str(uuid.uuid4()))
                        decision = record.get("decision", "UNKNOWN")
                        reason = record.get("reason", "")
                        symbol = record.get("symbol")

                        docs.append(
                            KnowledgeDocument(
                                document_id=f"journal_{entry_id}",
                                source_type=KnowledgeSourceType.DECISION_JOURNAL,
                                source_ref=entry_id,
                                symbol=symbol,
                                title=f"Decision {decision} - {symbol or 'System'}",
                                text=f"Decision: {decision}\nReason: {reason}",
                                created_at=datetime.fromisoformat(record.get("created_at", datetime.now().isoformat())),
                                updated_at=datetime.fromisoformat(record.get("created_at", datetime.now().isoformat()))
                            )
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        return docs

    def collect_from_review_thesis(self) -> list[KnowledgeDocument]:
        thesis_dir = self.data_dir / "review" / "theses"
        if not thesis_dir.exists():
            return []

        docs = []
        try:
            for tf in thesis_dir.glob("*.json"):
                try:
                    record = json.loads(tf.read_text(encoding="utf-8"))
                    thesis_id = record.get("thesis_id", tf.stem)
                    symbol = record.get("symbol")
                    strategy = record.get("strategy_name")
                    text = record.get("content", "")
                    if not text:
                        continue

                    docs.append(
                        KnowledgeDocument(
                            document_id=f"thesis_{thesis_id}",
                            source_type=KnowledgeSourceType.REVIEW_THESIS,
                            source_ref=thesis_id,
                            symbol=symbol,
                            strategy_name=strategy,
                            title=f"Thesis {symbol or 'System'}",
                            text=text,
                            created_at=datetime.fromisoformat(record.get("created_at", datetime.now().isoformat())),
                            updated_at=datetime.fromisoformat(record.get("updated_at", record.get("created_at", datetime.now().isoformat())))
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass

        return docs

    def collect_from_backtests(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_ensemble(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_portfolio_research(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_stress(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_drift(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_reports(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_governance(self) -> list[KnowledgeDocument]:
        return []

    def collect_from_research_lab(self) -> list[KnowledgeDocument]:
        return []
