import pandas as pd
from typing import Any, List, Dict
from bist_signal_bot.scanner.models import ScanReport, SymbolScanResult, ScanRankingItem, SymbolScanIssue

def scan_report_to_dict(report: ScanReport) -> Dict[str, Any]:
    # Custom dict generation to avoid pydantic issues with complex types and to keep it clean
    data = report.model_dump(mode='json')
    # Ensure nested objects are handled
    return data

def scan_results_to_dataframe(results: List[SymbolScanResult]) -> pd.DataFrame:
    data = []
    for r in results:
        sig = r.signal
        risk = r.risk_decision

        row = {
            "symbol": r.symbol,
            "status": r.status.value,
            "rank": r.rank,
            "rank_score": r.rank_score,
            "portfolio_status": r.portfolio_status,
            "signal_intent": sig.direction.value if sig else None,
            "signal_score": sig.score if sig else None,
            "confidence": sig.confidence if sig else None,
            "risk_status": risk.status.value if risk else None,
            "final_score": risk.final_score if risk else None,
            "reasons": " | ".join(r.reasons) if r.reasons else "",
            "elapsed_s": r.elapsed_seconds
        }
        data.append(row)
    return pd.DataFrame(data)

def scan_rankings_to_dataframe(rankings: List[ScanRankingItem]) -> pd.DataFrame:
    data = [r.dict() for r in rankings]
    return pd.DataFrame(data)

def scan_issues_to_dataframe(issues: List[SymbolScanIssue]) -> pd.DataFrame:
    data = [i.dict() for i in issues]
    return pd.DataFrame(data)

def _format_text_header(report: ScanReport) -> List[str]:
    return [
        "BIST Bot Signal Scan Report",
        "===========================",
        f"Strategy: {report.request.strategy_name}",
        f"Universe: {report.request.universe_mode.value}",
        f"Status: {report.status.value}",
        f"Total Symbols: {report.total_symbols} | Processed: {report.processed_symbols}",
        f"Passed: {report.passed_count} | Filtered: {report.filtered_count} | Rejected: {report.rejected_count} | Error: {report.error_count} | Watch: {report.watch_only_count}",
        "---------------------------",
        "Top Candidates:"
    ]

def _format_text_top_candidates(report: ScanReport) -> List[str]:
    lines = []
    top = report.top_candidates(report.request.top_n)
    if not top:
        lines.append("No passed candidates found.")
    else:
        for r in top:
            sig_dir = r.signal.direction.value if r.signal else "N/A"
            lines.append(f"  {r.rank}. {r.symbol} - {sig_dir} - Score: {r.rank_score:.1f} - Status: {r.status.value}")
    return lines

def _format_text_portfolio_summary(report: ScanReport) -> List[str]:
    lines = []
    if report.portfolio_decision:
        lines.append("---------------------------")
        lines.append("Portfolio Risk Summary:")
        lines.append(f"  Status: {report.portfolio_decision.status.value}")
        lines.append(f"  Allocations: {len(report.portfolio_decision.allocations)}")
    return lines

def format_scan_report_text(report: ScanReport) -> str:
    lines = []
    lines.extend(_format_text_header(report))
    lines.extend(_format_text_top_candidates(report))
    lines.extend(_format_text_portfolio_summary(report))
    lines.append("---------------------------")
    lines.append(report.disclaimer)
    return "\n".join(lines)


def _format_md_header_and_summary(report: ScanReport) -> List[str]:
    return [
        "# BIST Bot Signal Scan Report",
        "",
        f"**Strategy**: `{report.request.strategy_name}`",
        f"**Universe Mode**: `{report.request.universe_mode.value}`",
        f"**Source**: `{report.request.source}`",
        f"**Timeframe**: `{report.request.timeframe}`",
        f"**Started At**: `{report.started_at}`",
        f"**Elapsed**: `{report.elapsed_seconds:.2f}s`",
        "",
        "## Summary",
        f"- **Status**: `{report.status.value}`",
        f"- **Total Symbols**: {report.total_symbols}",
        f"- **Processed**: {report.processed_symbols}",
        f"- **Passed**: {report.passed_count}",
        f"- **Filtered**: {report.filtered_count}",
        f"- **Rejected**: {report.rejected_count}",
        f"- **Error**: {report.error_count}",
        f"- **Watch Only**: {report.watch_only_count}",
        "",
    ]

def _format_md_top_candidates(report: ScanReport) -> List[str]:
    lines = [
        "## Top Candidates",
        "| Rank | Symbol | Direction | Signal Score | Final Score | Status |",
        "|---|---|---|---|---|---|"
    ]
    top = report.top_candidates(report.request.top_n)
    for r in top:
        sig_dir = r.signal.direction.value if r.signal else "N/A"
        sig_score = f"{r.signal.score:.1f}" if r.signal and r.signal.score else "N/A"
        risk_score = f"{r.risk_decision.final_score:.1f}" if r.risk_decision and r.risk_decision.final_score else "N/A"
        lines.append(f"| {r.rank} | {r.symbol} | {sig_dir} | {sig_score} | {risk_score} | {r.status.value} |")
    lines.append("")
    return lines

def _format_md_portfolio_summary(report: ScanReport) -> List[str]:
    lines = []
    if report.portfolio_decision:
        lines.append("## Portfolio Risk Summary")
        lines.append(f"Status: **{report.portfolio_decision.status.value}**")
        if report.portfolio_decision.reasons:
            lines.append("Reasons:")
            for reason in report.portfolio_decision.reasons:
                lines.append(f"- {reason}")
        lines.append("")
    return lines

def _format_md_issues(report: ScanReport) -> List[str]:
    lines = []
    if report.issues:
        lines.append("## Issues")
        for iss in report.issues:
            lines.append(f"- **{iss.severity}** [{iss.stage}] {iss.symbol or 'System'}: {iss.message}")
        lines.append("")
    return lines

def format_scan_markdown(report: ScanReport) -> str:
    lines = []
    lines.extend(_format_md_header_and_summary(report))
    lines.extend(_format_md_top_candidates(report))
    lines.extend(_format_md_portfolio_summary(report))
    lines.extend(_format_md_issues(report))
    lines.append("---")
    lines.append(f"*{report.disclaimer}*")
    return "\n".join(lines)
