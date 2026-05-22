from typing import Any
import pandas as pd

from bist_signal_bot.knowledge.models import (
    AnalystMemoryCard,
    CaseLibraryResult,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeIndexBuildResult,
    KnowledgeSearchResult,
    KnowledgeSearchResultItem,
    SimilarCase
)

def knowledge_document_to_dict(document: KnowledgeDocument) -> dict[str, Any]:
    return document.model_dump()

def knowledge_chunk_to_dict(chunk: KnowledgeChunk) -> dict[str, Any]:
    return chunk.model_dump()

def search_result_to_dict(result: KnowledgeSearchResult) -> dict[str, Any]:
    return result.model_dump()

def search_item_to_dict(item: KnowledgeSearchResultItem) -> dict[str, Any]:
    return item.model_dump()

def similar_case_to_dict(case: SimilarCase) -> dict[str, Any]:
    return case.model_dump()

def case_library_result_to_dict(result: CaseLibraryResult) -> dict[str, Any]:
    return result.model_dump()

def memory_card_to_dict(card: AnalystMemoryCard) -> dict[str, Any]:
    return card.model_dump()

def index_build_result_to_dict(result: KnowledgeIndexBuildResult) -> dict[str, Any]:
    return result.model_dump()

def search_results_to_dataframe(items: list[KnowledgeSearchResultItem]) -> pd.DataFrame:
    data = [
        {
            "Rank": item.rank,
            "Title": item.title,
            "Source": item.source_type.value,
            "Symbol": item.symbol,
            "Score": round(item.score, 4),
            "Snippet": item.snippet[:50] + "..." if len(item.snippet) > 50 else item.snippet
        }
        for item in items
    ]
    return pd.DataFrame(data)

def similar_cases_to_dataframe(cases: list[SimilarCase]) -> pd.DataFrame:
    data = [
        {
            "Symbol": case.symbol,
            "Strategy": case.strategy_name,
            "Source": case.source_type.value,
            "Score": round(case.similarity_score, 4),
            "Outcome": case.outcome_summary
        }
        for case in cases
    ]
    return pd.DataFrame(data)

def format_search_result_text(result: KnowledgeSearchResult) -> str:
    lines = [
        f"Search Mode: {result.mode_used.value}",
        f"Matches: {result.total_matches}",
        f"Elapsed: {result.elapsed_seconds:.2f}s",
        "-" * 40
    ]

    for item in result.items[:5]:
        lines.append(f"[{item.rank}] {item.title} ({item.source_type.value}) - Score: {item.score:.4f}")
        lines.append(f"Snippet: {item.snippet}")
        lines.append("")

    lines.append(f"DISCLAIMER: {result.disclaimer}")
    return "\n".join(lines)

def format_similar_cases_text(result: CaseLibraryResult) -> str:
    lines = [f"Found {len(result.cases)} similar cases."]
    for case in result.cases[:3]:
        lines.append(f"- {case.title} (Score: {case.similarity_score:.2f})")
    lines.append("")
    lines.append(f"DISCLAIMER: {result.disclaimer}")
    return "\n".join(lines)

def format_memory_card_text(card: AnalystMemoryCard) -> str:
    lines = [
        f"Memory Card: {card.title}",
        f"Symbol: {card.symbol} | Strategy: {card.strategy_name}",
        "-" * 40,
        "Lessons:"
    ]
    for lesson in card.key_lessons:
        lines.append(f"- {lesson}")
    lines.append("\nPatterns:")
    for pat in card.repeated_patterns:
        lines.append(f"- {pat}")
    lines.append("\nRisks:")
    for r in card.risk_notes:
        lines.append(f"- {r}")
    lines.append("")
    lines.append(f"DISCLAIMER: {card.disclaimer}")
    return "\n".join(lines)

def format_index_build_text(result: KnowledgeIndexBuildResult) -> str:
    lines = [
        f"Index Build: {result.status.value}",
        f"Documents: {result.documents_indexed}/{result.documents_seen} (Skipped: {result.skipped_documents})",
        f"Chunks: {result.chunks_created}",
        f"Entries: {result.entries_indexed}",
        f"Elapsed: {result.elapsed_seconds:.2f}s"
    ]
    if result.errors:
        lines.append("Errors:")
        for e in result.errors:
            lines.append(f"- {e}")

    lines.append(f"\nDISCLAIMER: {result.disclaimer}")
    return "\n".join(lines)

def format_knowledge_report_markdown(stats: dict[str, Any]) -> str:
    return f"""## Research Knowledge Base Summary

- **Documents**: {stats.get('document_count', 0)}
- **Chunks**: {stats.get('chunk_count', 0)}
- **Memory Cards**: {stats.get('memory_card_count', 0)}
- **Last Build Status**: {stats.get('last_build_status', 'UNKNOWN')}

*Knowledge Base is research memory only. Not investment advice. No real order was sent.*
"""
