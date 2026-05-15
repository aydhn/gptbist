import pandas as pd
from typing import Any

from bist_signal_bot.quality.models import QualityRunResult, QualityCheckResult

def quality_run_result_to_dict(result: QualityRunResult) -> dict[str, Any]:
    return result.model_dump()

def quality_checks_to_dataframe(checks: list[QualityCheckResult]) -> pd.DataFrame:
    data = [
        {
            "check_name": c.check_name,
            "tool": c.tool.value,
            "status": c.status.value,
            "elapsed_seconds": c.elapsed_seconds,
            "exit_code": c.exit_code,
            "message": c.message
        }
        for c in checks
    ]
    return pd.DataFrame(data)

def format_quality_result_text(result: QualityRunResult) -> str:
    summary = result.summary()
    lines = [
        "=== BIST Bot Quality Gate Summary ===",
        f"Run ID: {summary['run_id']}",
        f"Status: {summary['status']}",
        f"Gate Level: {summary['gate_level']}",
        f"Suite: {summary['suite']}",
        f"Total Checks: {summary['checks_total']}",
        f"  Passed: {summary['checks_passed']}",
        f"  Warn:   {summary['checks_warn']}",
        f"  Failed: {summary['checks_failed']}",
        f"  Skipped:{summary['checks_skipped']}",
        f"Elapsed: {summary['elapsed_seconds']:.2f}s",
    ]

    if result.test_summary:
        ts = result.test_summary
        lines.append("\n--- Tests ---")
        lines.append(f"Total: {ts.total_tests}, Passed: {ts.passed}, Failed: {ts.failed}, Error: {ts.errors}, Skipped: {ts.skipped}")

    if result.coverage_summary and result.coverage_summary.measured:
        cs = result.coverage_summary
        lines.append("\n--- Coverage ---")
        lines.append(f"Total: {cs.total_coverage_pct}% (Threshold: {cs.threshold_pct}%) - Passed: {cs.passed_threshold}")

    if result.static_summary:
        ss = result.static_summary
        lines.append("\n--- Static Analysis ---")
        lines.append(f"Ruff: {ss.ruff_status.value}, Black: {ss.black_status.value}, Mypy: {ss.mypy_status.value}")

    lines.append(f"\n{result.disclaimer}")

    return "\n".join(lines)

def format_quality_markdown(result: QualityRunResult) -> str:
    lines = [
        "# BIST Signal Bot Quality Gate Report",
        "",
        f"> **Disclaimer:** {result.disclaimer}",
        "",
        "## Summary",
        f"- **Run ID:** `{result.run_id}`",
        f"- **Status:** **{result.status.value}**",
        f"- **Gate Level:** `{result.config.gate_level.value}`",
        f"- **Suite:** `{result.config.suite.value}`",
        f"- **Elapsed:** {result.elapsed_seconds:.2f}s",
        "",
        "## Checks Summary",
        f"- Total: {len(result.checks)}",
        f"- Passed: {len([c for c in result.checks if c.status.value == 'PASS'])}",
        f"- Warnings: {len([c for c in result.checks if c.status.value == 'WARN'])}",
        f"- Failed: {len(result.failed_checks())}",
        f"- Skipped: {len([c for c in result.checks if c.status.value == 'SKIP'])}",
        ""
    ]

    if result.test_summary:
        ts = result.test_summary
        lines.extend([
            "## Tests",
            f"- Total: {ts.total_tests}",
            f"- Passed: {ts.passed}",
            f"- Failed: {ts.failed}",
            f"- Errors: {ts.errors}",
            f"- Skipped: {ts.skipped}",
            ""
        ])

    if result.coverage_summary:
        cs = result.coverage_summary
        lines.extend([
            "## Coverage",
            f"- Enabled: {cs.enabled}",
            f"- Measured: {cs.measured}"
        ])
        if cs.measured:
            lines.extend([
                f"- Total: {cs.total_coverage_pct}%",
                f"- Threshold: {cs.threshold_pct}%",
                f"- Passed: {cs.passed_threshold}"
            ])
        lines.append("")

    if result.static_summary:
        ss = result.static_summary
        lines.extend([
            "## Static Analysis",
            f"- Ruff: {ss.ruff_status.value}",
            f"- Black: {ss.black_status.value}",
            f"- Mypy: {ss.mypy_status.value}",
            ""
        ])

    lines.extend([
        "## Check Details",
        "| Check Name | Tool | Status | Exit Code | Elapsed (s) | Message |",
        "|---|---|---|---|---|---|"
    ])

    for check in result.checks:
        lines.append(f"| {check.check_name} | {check.tool.value} | {check.status.value} | {check.exit_code or '-'} | {check.elapsed_seconds:.2f} | {check.message} |")

    failed = result.failed_checks()
    if failed:
        lines.extend([
            "",
            "## Failed Checks"
        ])
        for f in failed:
            lines.extend([
                f"### {f.check_name}",
                f"**Tool:** {f.tool.value} | **Status:** {f.status.value}",
                f"**Message:** {f.message}",
            ])
            if f.stderr_tail:
                lines.extend([
                    "**Stderr:**",
                    "```text",
                    f.stderr_tail,
                    "```"
                ])

    return "\n".join(lines)

def format_quality_check_text(check: QualityCheckResult) -> str:
    return f"[{check.status.value}] {check.check_name} ({check.tool.value}): {check.message} ({check.elapsed_seconds:.2f}s)"
