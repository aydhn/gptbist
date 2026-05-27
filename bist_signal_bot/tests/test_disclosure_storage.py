import pytest
from bist_signal_bot.disclosures.storage import DisclosureStore
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment, DisclosureImpactAssessment
from datetime import datetime

def test_disclosure_store_append_load_records(tmp_path):
    store = DisclosureStore(base_dir=tmp_path)
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Test", disclosure_type=DisclosureType.MATERIAL_EVENT, received_at=datetime.now(), source="test", language="tr", symbols=["ASELS"])
    store.append_record(record)
    records = store.load_records(symbol="ASELS")
    assert len(records) == 1
    assert records[0].disclosure_id == "1"

def test_disclosure_store_append_load_risk_tags(tmp_path):
    store = DisclosureStore(base_dir=tmp_path)
    tag = DisclosureRiskTag(tag_id="1", disclosure_id="1", tag_type=DisclosureRiskTagType.LEGAL_REGULATORY, severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE, message="Test")
    store.append_risk_tags([tag])
    tags = store.load_risk_tags(disclosure_id="1")
    assert len(tags) == 1
    assert tags[0].tag_id == "1"

def test_disclosure_store_append_load_impact(tmp_path):
    store = DisclosureStore(base_dir=tmp_path)
    assessment = DisclosureImpactAssessment(assessment_id="1", disclosure_id="1", disclosure_type=DisclosureType.MATERIAL_EVENT, sentiment=DisclosureSentiment.NEGATIVE, severity=DisclosureSeverity.HIGH, recommended_decision="REVIEW", symbols=["ASELS"])
    store.append_impact_assessment(assessment)
    assessments = store.load_impact_assessments(symbol="ASELS")
    assert len(assessments) == 1
    assert assessments[0].assessment_id == "1"
