import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureSentiment, DisclosureSeverity
from bist_signal_bot.disclosures.classifier import DisclosureClassifier

def test_classifier_financial_statement():
    classifier = DisclosureClassifier()
    record = DisclosureRecord(
        disclosure_id="123",
        title="Finansal Tablo Açıklaması",
        body="2023 Q1 bilanço detayları."
    )
    record = classifier.classify(record)
    assert record.disclosure_type == DisclosureType.FINANCIAL_STATEMENT
    assert record.severity == DisclosureSeverity.HIGH

def test_classifier_sentiment():
    classifier = DisclosureClassifier()

    # Positive
    record1 = DisclosureRecord(disclosure_id="1", title="Kâr artışı", body="Büyük ihale kazandı.")
    record1 = classifier.classify(record1)
    assert record1.sentiment == DisclosureSentiment.POSITIVE

    # Negative
    record2 = DisclosureRecord(disclosure_id="2", title="Zarar ve ceza", body="İptal edildi ve istifa.")
    record2 = classifier.classify(record2)
    assert record2.sentiment == DisclosureSentiment.NEGATIVE

def test_classifier_legal():
    classifier = DisclosureClassifier()
    record = DisclosureRecord(disclosure_id="123", title="Dava açıldı", body="Soruşturma başlatıldı.")
    record = classifier.classify(record)
    assert record.disclosure_type == DisclosureType.LEGAL_CASE
    assert record.severity == DisclosureSeverity.HIGH
