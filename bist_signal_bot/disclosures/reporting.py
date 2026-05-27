import pandas as pd
from typing import Any, Dict, List, Optional
from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureEntityLink,
    DisclosureRiskTag,
    DisclosureEventExtraction,
    DisclosureImpactAssessment,
    DisclosureDigest,
    DisclosureImportResult
)

def disclosure_to_dict(record: DisclosureRecord) -> Dict[str, Any]:
    return record.model_dump()

def entity_link_to_dict(link: DisclosureEntityLink) -> Dict[str, Any]:
    return link.model_dump()

def risk_tag_to_dict(tag: DisclosureRiskTag) -> Dict[str, Any]:
    return tag.model_dump()

def event_extraction_to_dict(extraction: DisclosureEventExtraction) -> Dict[str, Any]:
    return extraction.model_dump()

def impact_assessment_to_dict(assessment: DisclosureImpactAssessment) -> Dict[str, Any]:
    return assessment.model_dump()

def digest_to_dict(digest: DisclosureDigest) -> Dict[str, Any]:
    return digest.model_dump()

def import_result_to_dict(result: DisclosureImportResult) -> Dict[str, Any]:
    return result.model_dump()

def disclosures_to_dataframe(records: List[DisclosureRecord]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame([disclosure_to_dict(r) for r in records])
    return df

def risk_tags_to_dataframe(tags: List[DisclosureRiskTag]) -> pd.DataFrame:
    if not tags:
        return pd.DataFrame()
    return pd.DataFrame([risk_tag_to_dict(t) for t in tags])

def format_disclosure_text(record: DisclosureRecord) -> str:
    from bist_signal_bot.notifications.formatter import format_disclosure_record
    return format_disclosure_record(record)

def format_impact_assessment_text(assessment: DisclosureImpactAssessment) -> str:
    from bist_signal_bot.notifications.formatter import format_disclosure_impact_assessment
    return format_disclosure_impact_assessment(assessment)

def format_digest_text(digest: DisclosureDigest) -> str:
    from bist_signal_bot.notifications.formatter import format_disclosure_digest
    return format_disclosure_digest(digest)

def format_disclosure_report_markdown(records: List[DisclosureRecord], tags: List[DisclosureRiskTag], digests: Optional[List[DisclosureDigest]] = None) -> str:
    md = "# BIST Bot Disclosure Intelligence Report\n\n"
    md += "_Bu çıktı araştırma amaçlı duyuru özetidir. Yatırım tavsiyesi değildir. Gerçek emir gönderilmedi._\n\n"

    md += f"## Genel Bakış\n"
    md += f"- Toplam Duyuru: {len(records)}\n"
    md += f"- Toplam Risk Etiketi: {len(tags)}\n\n"

    if digests and len(digests) > 0:
        md += "## Son Özetler\n"
        for d in digests[:3]:
            md += f"### {d.title}\n"
            md += f"{d.summary}\n\n"
            for kp in d.key_points:
                md += f"- {kp}\n"
            md += "\n"

    md += "## Öne Çıkan Duyurular\n"
    for r in records[:10]:
        md += f"### [{','.join(r.symbols)}] {r.title} ({r.severity.value})\n"
        md += f"**Tip:** {r.disclosure_type.value} | **Sentiment:** {r.sentiment.value}\n\n"
        md += f"{r.body[:500]}...\n\n"

    return md
