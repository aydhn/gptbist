import pytest
from bist_signal_bot.research_lab.dependencies import ResearchJobDependencyResolver
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType

def test_dependency_topological_sort():
    resolver = ResearchJobDependencyResolver()
    j1 = ResearchJob(job_id="A", job_type=ResearchJobType.DATA_UPDATE, title="A")
    j2 = ResearchJob(job_id="B", job_type=ResearchJobType.BACKTEST, title="B", depends_on=["A"])
    j3 = ResearchJob(job_id="C", job_type=ResearchJobType.ADAPTIVE_RECOMMEND, title="C", depends_on=["B"])

    # Even if shuffled
    sorted_jobs = resolver.topological_sort([j3, j1, j2])
    assert sorted_jobs[0].job_id == "A"
    assert sorted_jobs[1].job_id == "B"
    assert sorted_jobs[2].job_id == "C"

def test_dependency_circular():
    resolver = ResearchJobDependencyResolver()
    j1 = ResearchJob(job_id="A", job_type=ResearchJobType.CUSTOM, title="A", depends_on=["B"])
    j2 = ResearchJob(job_id="B", job_type=ResearchJobType.CUSTOM, title="B", depends_on=["A"])

    errors = resolver.validate_graph([j1, j2])
    assert any("Circular" in str(e) for e in errors)
