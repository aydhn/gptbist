from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.storage import FinalHandoffStore
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder
from bist_signal_bot.final_handoff.operator_playbook import OperatorPlaybookBuilder
from bist_signal_bot.final_handoff.developer_playbook import DeveloperPlaybookBuilder
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.module_map import FinalModuleMapBuilder
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder
from bist_signal_bot.final_handoff.release_pack import FinalReleasePackBuilder
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder

def create_final_handoff_store(settings: Settings | None = None, base_dir: Path | None = None) -> FinalHandoffStore:
    return FinalHandoffStore(settings, base_dir)

def create_final_handoff_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalHandoffBuilder:
    return FinalHandoffBuilder(settings, base_dir)

def create_operator_playbook_builder(settings: Settings | None = None, base_dir: Path | None = None) -> OperatorPlaybookBuilder:
    return OperatorPlaybookBuilder(settings, base_dir)

def create_developer_playbook_builder(settings: Settings | None = None, base_dir: Path | None = None) -> DeveloperPlaybookBuilder:
    return DeveloperPlaybookBuilder(settings, base_dir)

def create_final_command_map_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalCommandMapBuilder:
    return FinalCommandMapBuilder(settings, base_dir)

def create_final_module_map_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalModuleMapBuilder:
    return FinalModuleMapBuilder(settings, base_dir)

def create_post_release_roadmap_builder(settings: Settings | None = None, base_dir: Path | None = None) -> PostReleaseRoadmapBuilder:
    return PostReleaseRoadmapBuilder(settings, base_dir)

def create_final_release_pack_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalReleasePackBuilder:
    return FinalReleasePackBuilder(settings, base_dir)

def create_maintenance_cadence_builder(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceCadenceBuilder:
    return MaintenanceCadenceBuilder(settings, base_dir)
