from pathlib import Path

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.data_catalog.contracts import DatasetContractRegistry
from bist_signal_bot.data_catalog.gates import DataQualityGateEngine
from bist_signal_bot.data_catalog.lineage import DataLineageTracker
from bist_signal_bot.data_catalog.profiler import DatasetProfiler
from bist_signal_bot.data_catalog.provenance import SourceProvenanceTracker
from bist_signal_bot.data_catalog.quality import DataQualityEngine
from bist_signal_bot.data_catalog.registry import DataCatalogRegistry
from bist_signal_bot.data_catalog.schema_drift import SchemaDriftDetector
from bist_signal_bot.data_catalog.storage import DataCatalogStore


def create_data_catalog_store(settings: Settings | None = None, base_dir: Path | None = None) -> DataCatalogStore:
    return DataCatalogStore(settings=settings, base_dir=base_dir)

def create_dataset_contract_registry(settings: Settings | None = None, base_dir: Path | None = None) -> DatasetContractRegistry:
    return DatasetContractRegistry(settings=settings, base_dir=base_dir)

def create_data_catalog_registry(settings: Settings | None = None, base_dir: Path | None = None) -> DataCatalogRegistry:
    return DataCatalogRegistry(settings=settings, base_dir=base_dir)

def create_dataset_profiler(settings: Settings | None = None, base_dir: Path | None = None) -> DatasetProfiler:
    return DatasetProfiler(settings=settings, base_dir=base_dir)

def create_data_quality_engine(settings: Settings | None = None, base_dir: Path | None = None) -> DataQualityEngine:
    return DataQualityEngine(settings=settings)

def create_schema_drift_detector(settings: Settings | None = None, base_dir: Path | None = None) -> SchemaDriftDetector:
    return SchemaDriftDetector(settings=settings)

def create_data_lineage_tracker(settings: Settings | None = None, base_dir: Path | None = None) -> DataLineageTracker:
    return DataLineageTracker(settings=settings)

def create_source_provenance_tracker(settings: Settings | None = None, base_dir: Path | None = None) -> SourceProvenanceTracker:
    return SourceProvenanceTracker(settings=settings, base_dir=base_dir)

def create_data_quality_gate_engine(settings: Settings | None = None, base_dir: Path | None = None) -> DataQualityGateEngine:
    return DataQualityGateEngine(settings=settings)
