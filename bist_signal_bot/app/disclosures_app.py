from pathlib import Path
from typing import Optional
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

def create_disclosure_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DisclosureStore:
    return DisclosureStore(settings=settings or get_settings(), base_dir=base_dir)

def create_disclosure_importer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DisclosureImporter:
    return DisclosureImporter(settings=settings or get_settings())

def create_disclosure_normalizer(settings: Optional[Settings] = None) -> DisclosureNormalizer:
    return DisclosureNormalizer(settings=settings or get_settings())

def create_disclosure_classifier(settings: Optional[Settings] = None) -> DisclosureClassifier:
    return DisclosureClassifier(settings=settings or get_settings())

def create_disclosure_entity_linker(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DisclosureEntityLinker:
    return DisclosureEntityLinker(settings=settings or get_settings(), base_dir=base_dir)

def create_disclosure_risk_tagger(settings: Optional[Settings] = None) -> DisclosureRiskTagger:
    return DisclosureRiskTagger(settings=settings or get_settings())

def create_disclosure_event_extractor(settings: Optional[Settings] = None) -> DisclosureEventExtractor:
    return DisclosureEventExtractor(settings=settings or get_settings())

def create_disclosure_impact_assessor(settings: Optional[Settings] = None) -> DisclosureImpactAssessor:
    return DisclosureImpactAssessor(settings=settings or get_settings())

def create_disclosure_digest_builder(settings: Optional[Settings] = None) -> DisclosureDigestBuilder:
    return DisclosureDigestBuilder(settings=settings or get_settings())
