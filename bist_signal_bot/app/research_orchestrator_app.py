from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research_orchestrator.storage import ResearchOrchestratorStore
from bist_signal_bot.research_orchestrator.planner import ResearchRunPlanner
from bist_signal_bot.research_orchestrator.dag import ResearchDAGBuilder
from bist_signal_bot.research_orchestrator.executor import ResearchRunExecutor
from bist_signal_bot.research_orchestrator.campaigns import ResearchCampaignRegistry
from bist_signal_bot.research_orchestrator.dependencies import ResearchDependencyResolver
from bist_signal_bot.research_orchestrator.guardrails import ResearchOrchestratorGuardrails
from bist_signal_bot.research_orchestrator.manifests import ResearchRunManifestBuilder
from bist_signal_bot.research_orchestrator.replay import ResearchRunReplayEngine

def create_research_orchestrator_store(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchOrchestratorStore:
    return ResearchOrchestratorStore(settings=settings, base_dir=base_dir)

def create_research_run_planner(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchRunPlanner:
    return ResearchRunPlanner()

def create_research_dag_builder(settings: Settings | None = None) -> ResearchDAGBuilder:
    return ResearchDAGBuilder()

def create_research_run_executor(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchRunExecutor:
    return ResearchRunExecutor()

def create_research_campaign_registry(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchCampaignRegistry:
    return ResearchCampaignRegistry()

def create_research_dependency_resolver(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchDependencyResolver:
    return ResearchDependencyResolver()

def create_research_orchestrator_guardrails(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchOrchestratorGuardrails:
    return ResearchOrchestratorGuardrails()

def create_research_run_manifest_builder(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchRunManifestBuilder:
    return ResearchRunManifestBuilder()

def create_research_run_replay_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchRunReplayEngine:
    return ResearchRunReplayEngine()
