import json
from typing import Any
from datetime import datetime

from bist_signal_bot.docs_hub.models import (
    DocPage, DocsIndex, DocsSearchResult, ArchitectureNode, ArchitectureEdge,
    ArchitectureMap, CommandCookbookEntry, CommandCookbook, TroubleshootingEntry,
    TroubleshootingKnowledgeBase, DocsCoverageResult, MVPHandoffManifest, DocsHubReport
)

def doc_page_to_dict(page: DocPage) -> dict[str, Any]:
    return json.loads(page.model_dump_json())

def docs_index_to_dict(index: DocsIndex) -> dict[str, Any]:
    return json.loads(index.model_dump_json())

def search_result_to_dict(result: DocsSearchResult) -> dict[str, Any]:
    return json.loads(result.model_dump_json())

def architecture_node_to_dict(node: ArchitectureNode) -> dict[str, Any]:
    return json.loads(node.model_dump_json())

def architecture_edge_to_dict(edge: ArchitectureEdge) -> dict[str, Any]:
    return json.loads(edge.model_dump_json())

def architecture_map_to_dict(amap: ArchitectureMap) -> dict[str, Any]:
    return json.loads(amap.model_dump_json())

def cookbook_entry_to_dict(entry: CommandCookbookEntry) -> dict[str, Any]:
    return json.loads(entry.model_dump_json())

def cookbook_to_dict(cookbook: CommandCookbook) -> dict[str, Any]:
    return json.loads(cookbook.model_dump_json())

def troubleshooting_entry_to_dict(entry: TroubleshootingEntry) -> dict[str, Any]:
    return json.loads(entry.model_dump_json())

def troubleshooting_kb_to_dict(kb: TroubleshootingKnowledgeBase) -> dict[str, Any]:
    return json.loads(kb.model_dump_json())

def coverage_to_dict(result: DocsCoverageResult) -> dict[str, Any]:
    return json.loads(result.model_dump_json())

def handoff_to_dict(manifest: MVPHandoffManifest) -> dict[str, Any]:
    return json.loads(manifest.model_dump_json())

def docs_hub_report_to_dict(report: DocsHubReport) -> dict[str, Any]:
    return json.loads(report.model_dump_json())

def format_docs_index_text(index: DocsIndex) -> str:
    return f"Indexed {index.total_pages} pages. {len(index.missing_expected_docs)} expected docs missing."

def format_search_results_text(result: DocsSearchResult) -> str:
    return f"Search for '{result.query}' found {len(result.matches)} matches."

def format_architecture_text(amap: ArchitectureMap) -> str:
    return f"Architecture Map: {amap.module_count} modules, {amap.command_count} commands."

def format_cookbook_text(cookbook: CommandCookbook) -> str:
    return f"Command Cookbook contains {len(cookbook.entries)} entries."

def format_troubleshooting_text(kb: TroubleshootingKnowledgeBase) -> str:
    return f"Troubleshooting KB contains {len(kb.entries)} entries."

def format_coverage_text(result: DocsCoverageResult) -> str:
    return f"Docs Coverage: {result.coverage_score}%"

def format_handoff_text(manifest: MVPHandoffManifest) -> str:
    return f"MVP Handoff QA Status: {manifest.qa_status}"

def _format_report_header(report: DocsHubReport) -> list[str]:
    return [
        f"# Documentation Hub Report ({report.generated_at})",
        "",
        "## Key Findings"
    ]

def _format_key_findings(findings: list[str]) -> list[str]:
    return [f"- {finding}" for finding in findings]

def _format_disclaimer(disclaimer: str) -> list[str]:
    return ["", "---", f"_{disclaimer}_"]

def format_docs_hub_report_markdown(report: DocsHubReport) -> str:
    lines = []
    lines.extend(_format_report_header(report))
    lines.extend(_format_key_findings(report.key_findings))
    lines.extend(_format_disclaimer(report.disclaimer))
    return "\n".join(lines)
