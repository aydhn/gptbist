import hashlib
from typing import List, Tuple
from datetime import datetime, timedelta
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobStatus

class ResearchJobDeduplicator:
    def build_dedupe_key(self, job: ResearchJob) -> str:
        parts = [
            str(job.job_type.value),
            ",".join(job.symbols),
            str(job.strategy_name),
            str(job.model_id),
            str(job.metadata.get('timeframe', '')),
            str(job.trigger.value)
        ]
        raw = "|".join(parts)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def is_duplicate(self, job: ResearchJob, existing_jobs: List[ResearchJob], window_hours: int) -> bool:
        if not job.dedupe_key:
             job.dedupe_key = self.build_dedupe_key(job)

        now = datetime.utcnow()
        cutoff = now - timedelta(hours=window_hours)

        for e in existing_jobs:
            if not e.dedupe_key:
                e.dedupe_key = self.build_dedupe_key(e)
            if e.dedupe_key == job.dedupe_key:
                 if e.created_at >= cutoff:
                      if e.status in [ResearchJobStatus.QUEUED, ResearchJobStatus.RUNNING, ResearchJobStatus.SUCCESS]:
                           return True
        return False

    def dedupe_jobs(self, jobs: List[ResearchJob], existing_jobs: List[ResearchJob], window_hours: int) -> Tuple[List[ResearchJob], List[ResearchJob]]:
        unique = []
        dupes = []
        for j in jobs:
            if self.is_duplicate(j, existing_jobs + unique, window_hours):
                dupes.append(j)
            else:
                unique.append(j)
        return unique, dupes
