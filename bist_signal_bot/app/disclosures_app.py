from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.storage import DisclosureStore
from bist_signal_bot.disclosures.importer import DisclosureImporter
from bist_signal_bot.disclosures.normalizer import DisclosureNormalizer
from bist_signal_bot.disclosures.classifier import DisclosureClassifier
from bist_signal_bot.disclosures.entity_linker import DisclosureEntityLinker
from bist_signal_bot.disclosures.risk_tags import DisclosureRiskTagger
from bist_signal_bot.disclosures.event_extractor import DisclosureEventExtractor
from bist_signal_bot.disclosures.impact import DisclosureImpactAssessor
from bist_signal_bot.disclosures.digest import DisclosureDigestBuilder

def create_disclosure_store(settings: Settings | None = None, base_dir: Path | None = None) -> DisclosureStore:
    return DisclosureStore(settings, base_dir)

def create_disclosure_importer(settings: Settings | None = None, base_dir: Path | None = None) -> DisclosureImporter:
    return DisclosureImporter()

def create_disclosure_normalizer(settings: Settings | None = None) -> DisclosureNormalizer:
    return DisclosureNormalizer()

def create_disclosure_classifier(settings: Settings | None = None) -> DisclosureClassifier:
    return DisclosureClassifier()

def create_disclosure_entity_linker(settings: Settings | None = None, base_dir: Path | None = None) -> DisclosureEntityLinker:
    return DisclosureEntityLinker()

def create_disclosure_risk_tagger(settings: Settings | None = None) -> DisclosureRiskTagger:
    return DisclosureRiskTagger()

def create_disclosure_event_extractor(settings: Settings | None = None) -> DisclosureEventExtractor:
    return DisclosureEventExtractor()

def create_disclosure_impact_assessor(settings: Settings | None = None) -> DisclosureImpactAssessor:
    return DisclosureImpactAssessor()

def create_disclosure_digest_builder(settings: Settings | None = None) -> DisclosureDigestBuilder:
    return DisclosureDigestBuilder()
