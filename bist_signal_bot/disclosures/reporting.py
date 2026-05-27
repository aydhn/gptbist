from typing import Any, List, Optional
import pandas as pd
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureEntityLink, DisclosureRiskTag,
    DisclosureEventExtraction, DisclosureImpactAssessment, DisclosureDigest, DisclosureImportResult
)

def disclosure_to_dict(record: DisclosureRecord) -> dict[str, Any]:
    return record.dict()

def entity_link_to_dict(link: DisclosureEntityLink) -> dict[str, Any]:
    return link.dict()

def risk_tag_to_dict(tag: DisclosureRiskTag) -> dict[str, Any]:
    return tag.dict()

def event_extraction_to_dict(extraction: DisclosureEventExtraction) -> dict[str, Any]:
    return extraction.dict()

def impact_assessment_to_dict(assessment: DisclosureImpactAssessment) -> dict[str, Any]:
    return assessment.dict()

def digest_to_dict(digest: DisclosureDigest) -> dict[str, Any]:
    return digest.dict()

def import_result_to_dict(result: DisclosureImportResult) -> dict[str, Any]:
    return result.dict()

def disclosures_to_dataframe(records: List[DisclosureRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.dict() for r in records])

def risk_tags_to_dataframe(tags: List[DisclosureRiskTag]) -> pd.DataFrame:
    return pd.DataFrame([t.dict() for t in tags])

def format_disclosure_text(record: DisclosureRecord) -> str:
    return f"[{record.disclosure_type.value}] {record.title}"

def format_impact_assessment_text(assessment: DisclosureImpactAssessment) -> str:
    return f"Assessment for {assessment.disclosure_id}: Score {assessment.narrative_risk_score}"

def format_digest_text(digest: DisclosureDigest) -> str:
    return f"{digest.title}: {digest.summary}"

def format_disclosure_report_markdown(records: List[DisclosureRecord], tags: List[DisclosureRiskTag], digests: Optional[List[DisclosureDigest]] = None) -> str:
    md = "# Disclosure Report\n\n"
    for r in records:
        md += f"## {r.title}\n{r.body}\n\n"
    md += "\n\n*Disclosure record is local research metadata only. It is not investment advice. No real order was sent.*\n"
    return md
