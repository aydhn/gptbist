from pathlib import Path
from typing import Optional

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

def create_final_handoff_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FinalHandoffStore:
    return FinalHandoffStore(settings=settings, base_dir=base_dir)

def create_final_handoff_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FinalHandoffBuilder:
    # base_dir is not used in FinalHandoffBuilder currently, but keeping signature consistent
    return FinalHandoffBuilder(settings=settings)

def create_operator_playbook_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> OperatorPlaybookBuilder:
    return OperatorPlaybookBuilder(settings=settings)

def create_developer_playbook_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DeveloperPlaybookBuilder:
    return DeveloperPlaybookBuilder(settings=settings)

def create_final_command_map_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FinalCommandMapBuilder:
    return FinalCommandMapBuilder(settings=settings)

def create_final_module_map_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FinalModuleMapBuilder:
    return FinalModuleMapBuilder(settings=settings)

def create_post_release_roadmap_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PostReleaseRoadmapBuilder:
    return PostReleaseRoadmapBuilder(settings=settings)

def create_final_release_pack_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FinalReleasePackBuilder:
    return FinalReleasePackBuilder(settings=settings, base_dir=base_dir)

def create_maintenance_cadence_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceCadenceBuilder:
    return MaintenanceCadenceBuilder(settings=settings)
