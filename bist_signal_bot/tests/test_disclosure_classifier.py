import pytest
from bist_signal_bot.disclosures.classifier import DisclosureClassifier
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureSentiment
from datetime import datetime

def test_disclosure_classifier_financial_statement():
    classifier = DisclosureClassifier()
    record = DisclosureRecord(disclosure_id="1", title="Finansal Rapor", body="Bilanço", received_at=datetime.now(), source="test", language="tr")
    classified = classifier.classify(record)
    assert classified.disclosure_type == DisclosureType.FINANCIAL_STATEMENT

def test_disclosure_classifier_dividend():
    classifier = DisclosureClassifier()
    record = DisclosureRecord(disclosure_id="1", title="Kar Payı Dağıtımı", body="Temettü ödenecek.", received_at=datetime.now(), source="test", language="tr")
    classified = classifier.classify(record)
    assert classified.disclosure_type == DisclosureType.DIVIDEND

def test_disclosure_classifier_legal():
    classifier = DisclosureClassifier()
    record = DisclosureRecord(disclosure_id="1", title="Dava Süreci", body="Mahkeme kararı.", received_at=datetime.now(), source="test", language="tr")
    classified = classifier.classify(record)
    assert classified.disclosure_type == DisclosureType.LEGAL_CASE

def test_disclosure_classifier_sentiment():
    classifier = DisclosureClassifier()
    assert classifier.classify_sentiment("İhale", "Büyük bir ihale kazanıldı.") == DisclosureSentiment.POSITIVE
    assert classifier.classify_sentiment("Ceza", "SPK tarafından ceza kesildi.") == DisclosureSentiment.NEGATIVE
