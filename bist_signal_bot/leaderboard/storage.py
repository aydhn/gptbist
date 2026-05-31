import json
from pathlib import Path
from datetime import datetime
from typing import Any
from bist_signal_bot.leaderboard.models import (
    BenchmarkCohort, ResearchCandidate, CandidateScore, ResearchLeaderboard,
    CandidateComparison, SelectionPolicy, CandidateSelectionResult, LeaderboardReport, CandidateType
)
from bist_signal_bot.storage.paths import get_leaderboard_dir
from bist_signal_bot.core.exceptions import LeaderboardStorageError

class LeaderboardStore:
    def __init__(self, settings=None, base_dir: Path | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_leaderboard_dir(self.settings)

    def _get_file(self, subdir: str, filename: str) -> Path:
        d = self.base_dir / subdir
        d.mkdir(parents=True, exist_ok=True)
        return d / filename

    def _append_jsonl(self, path: Path, obj: Any):
        with open(path, "a", encoding="utf-8") as f:
            f.write(obj.model_dump_json() + "\n")

    def _read_jsonl(self, path: Path, model_class, limit: int = 10000) -> list:
        if not path.exists():
            return []
        items = []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) > limit:
                lines = lines[-limit:]
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        items.append(model_class.model_validate_json(line))
                    except Exception:
                        pass
        return items

    def append_cohort(self, cohort: BenchmarkCohort) -> Path:
        p = self._get_file("cohorts", "benchmark_cohorts.jsonl")
        self._append_jsonl(p, cohort)
        return p

    def load_cohorts(self, limit: int = 10000) -> list[BenchmarkCohort]:
        return self._read_jsonl(self._get_file("cohorts", "benchmark_cohorts.jsonl"), BenchmarkCohort, limit)

    def append_candidate(self, candidate: ResearchCandidate) -> Path:
        p = self._get_file("candidates", "research_candidates.jsonl")
        self._append_jsonl(p, candidate)
        return p

    def load_candidates(self, candidate_type: CandidateType | None = None, limit: int = 10000) -> list[ResearchCandidate]:
        all_cands = self._read_jsonl(self._get_file("candidates", "research_candidates.jsonl"), ResearchCandidate, limit)
        if candidate_type:
            return [c for c in all_cands if c.candidate_type == candidate_type]
        return all_cands

    def append_score(self, score: CandidateScore) -> Path:
        p = self._get_file("scores", "candidate_scores.jsonl")
        self._append_jsonl(p, score)
        return p

    def load_scores(self, candidate_id: str | None = None, limit: int = 10000) -> list[CandidateScore]:
        all_scores = self._read_jsonl(self._get_file("scores", "candidate_scores.jsonl"), CandidateScore, limit)
        if candidate_id:
            return [s for s in all_scores if s.candidate_id == candidate_id]
        return all_scores

    def append_leaderboard(self, leaderboard: ResearchLeaderboard) -> Path:
        p = self._get_file("leaderboards", "research_leaderboards.jsonl")
        self._append_jsonl(p, leaderboard)
        return p

    def load_leaderboards(self, cohort_id: str | None = None, limit: int = 1000) -> list[ResearchLeaderboard]:
        all_lbs = self._read_jsonl(self._get_file("leaderboards", "research_leaderboards.jsonl"), ResearchLeaderboard, limit)
        if cohort_id:
            return [l for l in all_lbs if l.cohort_id == cohort_id]
        return all_lbs

    def load_latest_leaderboard(self, cohort_id: str | None = None) -> ResearchLeaderboard | None:
        lbs = self.load_leaderboards(cohort_id, limit=100)
        if not lbs:
            return None
        return lbs[-1]

    def append_comparison(self, comparison: CandidateComparison) -> Path:
        p = self._get_file("comparisons", "candidate_comparisons.jsonl")
        self._append_jsonl(p, comparison)
        return p

    def save_policies(self, policies: list[SelectionPolicy]) -> Path:
        p = self._get_file("policies", "selection_policies.json")
        data = [pol.model_dump() for pol in policies]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return p

    def load_policies(self) -> list[SelectionPolicy]:
        p = self._get_file("policies", "selection_policies.json")
        if not p.exists():
            return []
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [SelectionPolicy.model_validate(d) for d in data]
        except Exception:
            return []

    def append_selection(self, result: CandidateSelectionResult) -> Path:
        p = self._get_file("selections", "candidate_selection_results.jsonl")
        self._append_jsonl(p, result)
        return p

    def load_selections(self, limit: int = 10000) -> list[CandidateSelectionResult]:
        return self._read_jsonl(self._get_file("selections", "candidate_selection_results.jsonl"), CandidateSelectionResult, limit)

    def save_report(self, report: LeaderboardReport, markdown_text: str) -> dict[str, Path]:
        date_str = datetime.now().strftime('%Y%m%d')
        d = self._get_file(f"reports/{date_str}", "")
        d.mkdir(parents=True, exist_ok=True)

        md_path = d / "leaderboard_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        json_path = d / "leaderboard_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_path, "json": json_path}
