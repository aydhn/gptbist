import json
from pathlib import Path
from typing import Any
from bist_signal_bot.explainability.models import SignalExplanation, EvidenceCard, DecisionTrace

class ExplainabilityStore:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        if base_dir is None:
            self.base_dir = Path("data/explainability")
        else:
            self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.signals_dir = self.base_dir / "signal_explanations"
        self.cards_dir = self.base_dir / "evidence_cards"
        self.traces_dir = self.base_dir / "decision_traces"
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self.cards_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)

        self.signals_file = self.signals_dir / "signal_explanations.jsonl"
        self.cards_file = self.cards_dir / "evidence_cards.jsonl"
        self.traces_file = self.traces_dir / "decision_traces.jsonl"

    def append_signal_explanation(self, explanation: SignalExplanation) -> Path:
        with open(self.signals_file, "a") as f:
            f.write(explanation.model_dump_json() + "\n")
        return self.signals_file

    def load_signal_explanations(self, symbol: str | None = None, strategy_name: str | None = None, limit: int = 1000) -> list[SignalExplanation]:
        if not self.signals_file.exists():
            return []
        res = []
        with open(self.signals_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if symbol and data.get("symbol") != symbol: continue
                if strategy_name and data.get("strategy_name") != strategy_name: continue
                res.append(SignalExplanation(**data))
        return res[-limit:]

    def get_signal_explanation(self, explanation_id: str) -> SignalExplanation | None:
        for ex in self.load_signal_explanations():
            if ex.explanation_id == explanation_id:
                return ex
        return None

    def append_evidence_card(self, card: EvidenceCard) -> Path:
        with open(self.cards_file, "a") as f:
            f.write(card.model_dump_json() + "\n")
        return self.cards_file

    def load_evidence_cards(self, symbol: str | None = None, limit: int = 1000) -> list[EvidenceCard]:
        if not self.cards_file.exists():
            return []
        res = []
        with open(self.cards_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if symbol and data.get("symbol") != symbol: continue
                res.append(EvidenceCard(**data))
        return res[-limit:]

    def get_evidence_card(self, card_id: str) -> EvidenceCard | None:
        for c in self.load_evidence_cards():
            if c.card_id == card_id:
                return c
        return None

    def append_decision_trace(self, trace: DecisionTrace) -> Path:
        with open(self.traces_file, "a") as f:
            f.write(trace.model_dump_json() + "\n")
        return self.traces_file

    def load_decision_traces(self, symbol: str | None = None, limit: int = 1000) -> list[DecisionTrace]:
        if not self.traces_file.exists():
            return []
        res = []
        with open(self.traces_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if symbol and data.get("symbol") != symbol: continue
                res.append(DecisionTrace(**data))
        return res[-limit:]

    def get_decision_trace(self, trace_id: str) -> DecisionTrace | None:
        for t in self.load_decision_traces():
            if t.trace_id == trace_id:
                return t
        return None
