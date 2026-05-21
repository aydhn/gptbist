from typing import List, Optional
from bist_signal_bot.research_lab.models import ResearchJob, ResearchBatchPlan, ResearchJobStatus, ResearchJobResult
from bist_signal_bot.research_lab.storage import ResearchLabStore
from bist_signal_bot.core.exceptions import ResearchQueueError

class ResearchJobQueue:
    def __init__(self, settings=None, base_dir=None):
        self.store = ResearchLabStore(settings, base_dir)

    def enqueue(self, job: ResearchJob) -> ResearchJob:
        job.status = ResearchJobStatus.QUEUED
        self.store.append_job(job)
        return job

    def enqueue_plan(self, plan: ResearchBatchPlan) -> List[ResearchJob]:
        queued = []
        for j in plan.jobs:
             queued.append(self.enqueue(j))
        self.store.save_plan(plan)
        return queued

    def list_jobs(self, status: Optional[ResearchJobStatus] = None, limit: int = 100) -> List[ResearchJob]:
        jobs = self.store.load_jobs(limit=limit)
        if status:
             return [j for j in jobs if j.status == status]
        return jobs

    def get_job(self, job_id: str) -> Optional[ResearchJob]:
        jobs = self.list_jobs(limit=1000)
        for j in jobs:
            if j.job_id == job_id:
                return j
        return None

    def update_job(self, job: ResearchJob) -> ResearchJob:
        self.store.update_job(job)
        return job

    def cancel_job(self, job_id: str, confirm: bool = False) -> ResearchJob:
        if not confirm:
            raise ResearchQueueError("Cannot cancel job without confirmation")
        job = self.get_job(job_id)
        if not job:
            raise ResearchQueueError(f"Job {job_id} not found")
        if job.status in [ResearchJobStatus.SUCCESS, ResearchJobStatus.FAILED, ResearchJobStatus.CANCELLED]:
            raise ResearchQueueError(f"Cannot cancel job in state {job.status}")

        job.status = ResearchJobStatus.CANCELLED
        return self.update_job(job)

    def pop_next_ready_jobs(self, limit: int = 1) -> List[ResearchJob]:
        from bist_signal_bot.research_lab.dependencies import ResearchJobDependencyResolver
        resolver = ResearchJobDependencyResolver()
        all_jobs = self.list_jobs(limit=1000)

        ready = []
        for j in all_jobs:
            if j.status == ResearchJobStatus.QUEUED:
                deps_met = True
                for dep in j.depends_on:
                    dep_job = next((dj for dj in all_jobs if dj.job_id == dep), None)
                    if dep_job and dep_job.status != ResearchJobStatus.SUCCESS:
                        deps_met = False
                        break
                if deps_met:
                    ready.append(j)

        sorted_ready = resolver.topological_sort(ready)
        priority_map = {"URGENT": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
        sorted_ready.sort(key=lambda x: priority_map.get(x.priority.value, 0), reverse=True)

        popped = sorted_ready[:limit]
        for p in popped:
            p.status = ResearchJobStatus.RUNNING
            self.update_job(p)

        return popped

    def mark_result(self, job_id: str, result: ResearchJobResult) -> ResearchJob:
        job = self.get_job(job_id)
        if not job:
            raise ResearchQueueError(f"Job {job_id} not found")

        job.status = result.status
        if result.finished_at:
             job.finished_at = result.finished_at
        self.update_job(job)
        self.store.append_result(result)
        return job
