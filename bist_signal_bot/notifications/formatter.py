from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureImpactAssessment, DisclosureDigest

def format_disclosure_record(record: DisclosureRecord) -> str:
    tags_str = ", ".join(record.tags) if record.tags else "None"
    return f"""BIST Bot Disclosure Özeti
Sembol: {','.join(record.symbols)}
Tip: {record.disclosure_type.value}
Severity: {record.severity.value}
Tags: {tags_str}

Bu çıktı araştırma amaçlı duyuru özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.
"""

def format_disclosure_impact_assessment(assessment: DisclosureImpactAssessment) -> str:
    tags_str = ", ".join([t.tag_type.value for t in assessment.risk_tags])
    return f"""BIST Bot Disclosure Impact Özeti
Sembol: {','.join(assessment.symbols)}
Tip: {assessment.disclosure_type.value}
Severity: {assessment.severity.value}
Narrative Risk Score: {assessment.narrative_risk_score}
Risk Tags: {tags_str}

Bu çıktı araştırma amaçlı duyuru özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.
"""

def format_disclosure_digest(digest: DisclosureDigest) -> str:
    return f"""BIST Bot Disclosure Digest
Title: {digest.title}
High Severity: {digest.high_severity_count}
Summary: {digest.summary}

Bu çıktı araştırma amaçlı duyuru özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.
"""
