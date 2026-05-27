import pandas as pd
from typing import List, Dict, Any, Optional
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureEntityLink, DisclosureRiskTag, DisclosureEventExtraction,
    DisclosureImpactAssessment, DisclosureDigest, DisclosureImportResult
)

def disclosure_to_dict(record: DisclosureRecord) -> Dict[str, Any]: return record.model_dump()
def entity_link_to_dict(link: DisclosureEntityLink) -> Dict[str, Any]: return link.model_dump()
def risk_tag_to_dict(tag: DisclosureRiskTag) -> Dict[str, Any]: return tag.model_dump()
def event_extraction_to_dict(extraction: DisclosureEventExtraction) -> Dict[str, Any]: return extraction.model_dump()
def impact_assessment_to_dict(assessment: DisclosureImpactAssessment) -> Dict[str, Any]: return assessment.model_dump()
def digest_to_dict(digest: DisclosureDigest) -> Dict[str, Any]: return digest.model_dump()
def import_result_to_dict(result: DisclosureImportResult) -> Dict[str, Any]: return result.model_dump()

def disclosures_to_dataframe(records: List[DisclosureRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in records])

def risk_tags_to_dataframe(tags: List[DisclosureRiskTag]) -> pd.DataFrame:
    return pd.DataFrame([t.model_dump() for t in tags])

def format_disclosure_text(record: DisclosureRecord) -> str:
    lines = [
        f"Disclosure: {record.title}", f"ID: {record.disclosure_id}", f"Type: {record.disclosure_type.value}",
        f"Symbols: {', '.join(record.symbols) if record.symbols else 'None'}", f"Severity: {record.severity.value}",
        f"Sentiment: {record.sentiment.value}", f"\n{record.body[:500]}..." if len(record.body) > 500 else f"\n{record.body}",
        f"\nDisclaimer: {record.disclaimer}"
    ]
    return "\n".join(lines)

def format_impact_assessment_text(assessment: DisclosureImpactAssessment) -> str:
    lines = [
        f"Impact Assessment for: {assessment.disclosure_id}", f"Narrative Risk Score: {assessment.narrative_risk_score}",
        f"Decision: {assessment.recommended_decision}", f"Risk Tags: {len(assessment.risk_tags)}"
    ]
    for t in assessment.risk_tags: lines.append(f" - [{t.severity.value}] {t.tag_type.value}: {t.message}")
    lines.append(f"\nDisclaimer: {assessment.disclaimer}")
    return "\n".join(lines)

def format_digest_text(digest: DisclosureDigest) -> str:
    lines = [f"Digest: {digest.title}", f"Summary: {digest.summary}", "Key Points:"]
    for kp in digest.key_points: lines.append(f" - {kp}")
    lines.append(f"\nDisclaimer: {digest.disclaimer}")
    return "\n".join(lines)

def format_disclosure_report_markdown(records: List[DisclosureRecord], tags: List[DisclosureRiskTag], digests: Optional[List[DisclosureDigest]] = None) -> str:
    lines = ["# Disclosure Intelligence Report", ""]
    if digests:
        lines.append("## Latest Digests")
        for d in digests:
            lines.append(f"### {d.title}"); lines.append(f"*{d.summary}*"); lines.append("")
            for kp in d.key_points: lines.append(f"- {kp}")
            lines.append("")
    lines.append("## High Severity Risks")
    high_tags = [t for t in tags if t.severity.value in ["HIGH", "CRITICAL"]]
    if high_tags:
        for t in high_tags: lines.append(f"- **{t.tag_type.value}**: {t.message}")
    else: lines.append("*None*")
    lines.append("")
    lines.append("## Recent Disclosures")
    for r in records[:10]: lines.append(f"- **{r.title}** ({r.disclosure_type.value}) - Severity: {r.severity.value}")
    lines.append(""); lines.append("---"); lines.append(f"*{records[0].disclaimer if records else 'Research-only data.'}*")
    return "\n".join(lines)