from bist_signal_bot.disclosures.classifier import DisclosureClassifier
from bist_signal_bot.disclosures.models import DisclosureType, DisclosureSentiment
def test_classifier_type():
    clf = DisclosureClassifier()
    assert clf.classify_type("Faaliyet Raporu Özeti", "") == DisclosureType.FINANCIAL_STATEMENT
    assert clf.classify_type("Sermaye Artırımı", "Bedelli yapılacak.") == DisclosureType.CAPITAL_INCREASE
