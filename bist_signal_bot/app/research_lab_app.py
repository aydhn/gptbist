from typing import Optional
from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.research_lab.policy import ResearchLabPolicyManager
from bist_signal_bot.research_lab.planner import ResearchJobPlanner
from bist_signal_bot.research_lab.queue import ResearchJobQueue
from bist_signal_bot.research_lab.executor import ResearchJobExecutor
from bist_signal_bot.research_lab.storage import ResearchLabStore

def create_research_lab_policy_manager(settings: Optional[Settings] = None) -> ResearchLabPolicyManager:
    return ResearchLabPolicyManager(settings)

def create_research_job_planner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ResearchJobPlanner:
    return ResearchJobPlanner(settings, base_dir)

def create_research_job_queue(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ResearchJobQueue:
    return ResearchJobQueue(settings, base_dir)

def create_research_job_executor(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ResearchJobExecutor:
    return ResearchJobExecutor(settings, base_dir)

def create_research_lab_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ResearchLabStore:
    return ResearchLabStore(settings, base_dir)
