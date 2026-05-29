from bist_signal_bot.review_workflow.reporting import format_review_case_text, format_review_workflow_report_markdown
from bist_signal_bot.review_workflow.models import ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority, ReviewWorkflowReport

def test_format_review_case_text():
    case = ReviewCase(
        case_id="1",
        title="T",
        summary="S",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.MEDIUM,
        symbol="ASELS",
        conflicts=["MACRO"]
    )
    text = format_review_case_text(case)
    assert "Symbol: ASELS" in text
    assert "Priority: MEDIUM" in text
    assert "Disclaimer: Review case is research-only." in text

def test_format_report_markdown():
    report = ReviewWorkflowReport(
        report_id="1",
        key_findings=["Missing data for THYAO"]
    )
    md = format_review_workflow_report_markdown(report)
    assert "Review Workflow Report" in md
    assert "Missing data for THYAO" in md
    assert "Disclaimer" in md
    assert "research-only" in md
