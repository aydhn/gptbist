import pandas as pd
from typing import Any, Dict, List
from bist_signal_bot.context_fusion.models import (
    ContextSourceRef, ContextSignal, ContextLayerSummary,
    ContextConflict, EvidenceGap, ResearchGraphNode, ResearchGraphEdge,
    ResearchGraph, CompositeResearchScore, UnifiedContextSnapshot,
    ContextFusionReport
)

def source_ref_to_dict(ref: ContextSourceRef) -> Dict[str, Any]:
    return ref.model_dump()

def context_signal_to_dict(signal: ContextSignal) -> Dict[str, Any]:
    return signal.model_dump()

def layer_summary_to_dict(summary: ContextLayerSummary) -> Dict[str, Any]:
    return summary.model_dump()

def conflict_to_dict(conflict: ContextConflict) -> Dict[str, Any]:
    return conflict.model_dump()

def gap_to_dict(gap: EvidenceGap) -> Dict[str, Any]:
    return gap.model_dump()

def graph_node_to_dict(node: ResearchGraphNode) -> Dict[str, Any]:
    return node.model_dump()

def graph_edge_to_dict(edge: ResearchGraphEdge) -> Dict[str, Any]:
    return edge.model_dump()

def research_graph_to_dict(graph: ResearchGraph) -> Dict[str, Any]:
    return graph.model_dump()

def composite_score_to_dict(score: CompositeResearchScore) -> Dict[str, Any]:
    return score.model_dump()

def snapshot_to_dict(snapshot: UnifiedContextSnapshot) -> Dict[str, Any]:
    return snapshot.safe_public_dict()

def context_report_to_dict(report: ContextFusionReport) -> Dict[str, Any]:
    return report.model_dump()

def context_signals_to_dataframe(signals: List[ContextSignal]) -> pd.DataFrame:
    data = []
    for s in signals:
        row = {
            "Layer": s.layer.value,
            "Title": s.title,
            "Score": s.normalized_score,
            "Direction": s.direction.value,
            "Status": s.status.value,
            "Message": s.message
        }
        data.append(row)
    return pd.DataFrame(data)

def conflicts_to_dataframe(conflicts: List[ContextConflict]) -> pd.DataFrame:
    data = []
    for c in conflicts:
        row = {
            "Type": c.conflict_type.value,
            "Symbol": c.symbol,
            "Severity": c.severity.value,
            "Impact": c.score_impact,
            "Message": c.message
        }
        data.append(row)
    return pd.DataFrame(data)

def gaps_to_dataframe(gaps: List[EvidenceGap]) -> pd.DataFrame:
    data = []
    for g in gaps:
        row = {
            "Type": g.gap_type.value,
            "Layer": g.layer.value,
            "Symbol": g.symbol,
            "Severity": g.severity.value,
            "Message": g.message
        }
        data.append(row)
    return pd.DataFrame(data)

def format_context_snapshot_text(snapshot: UnifiedContextSnapshot) -> str:
    lines = [
        f"=== UNIFIED CONTEXT SNAPSHOT: {snapshot.symbol} ===",
        f"As Of: {snapshot.as_of.isoformat()}",
    ]
    if snapshot.composite_score:
        lines.append(f"Composite Score: {snapshot.composite_score.adjusted_score:.2f} ({snapshot.composite_score.final_status.value})")

    lines.append(f"Key Supports: {', '.join(snapshot.key_supports) if snapshot.key_supports else 'None'}")
    lines.append(f"Key Pressures: {', '.join(snapshot.key_pressures) if snapshot.key_pressures else 'None'}")

    if snapshot.required_reviews:
        lines.append("Required Reviews:")
        for r in snapshot.required_reviews:
            lines.append(f"  - {r}")

    lines.append("\n" + snapshot.disclaimer)
    return "\n".join(lines)

def format_conflicts_text(conflicts: List[ContextConflict]) -> str:
    if not conflicts:
        return "No conflicts detected."
    lines = []
    for c in conflicts:
        lines.append(f"[{c.severity.value}] {c.conflict_type.value}: {c.message}")
    if conflicts:
        lines.append("\n" + conflicts[0].disclaimer)
    return "\n".join(lines)

def format_evidence_gaps_text(gaps: List[EvidenceGap]) -> str:
    if not gaps:
        return "No evidence gaps detected."
    lines = []
    for g in gaps:
        lines.append(f"[{g.severity.value}] {g.gap_type.value} ({g.layer.value}): {g.message}")
    return "\n".join(lines)

def format_research_graph_text(graph: ResearchGraph) -> str:
    lines = [f"=== RESEARCH GRAPH: {graph.symbol} ===", f"Nodes: {len(graph.nodes)} | Edges: {len(graph.edges)}"]
    for e in graph.edges:
        from_node = next((n.label for n in graph.nodes if n.node_id == e.from_node_id), e.from_node_id)
        to_node = next((n.label for n in graph.nodes if n.node_id == e.to_node_id), e.to_node_id)
        lines.append(f"  {from_node} --[{e.relationship}]--> {to_node}")
    lines.append("\n" + graph.disclaimer)
    return "\n".join(lines)

def format_context_fusion_report_markdown(report: ContextFusionReport) -> str:
    md = [
        f"# Context Fusion Report",
        f"Generated At: {report.generated_at.isoformat()}\n",
        "## Key Findings"
    ]
    for kf in report.key_findings:
        md.append(f"- {kf}")

    md.append("\n## Top Snapshots")
    for s in report.snapshots[:5]:
        score = f"{s.composite_score.adjusted_score:.2f}" if s.composite_score else "N/A"
        md.append(f"### {s.symbol} (Score: {score})")
        md.append(f"- Status: {s.composite_score.final_status.value if s.composite_score else 'N/A'}")
        md.append(f"- Supports: {', '.join(s.key_supports)}")
        md.append(f"- Pressures: {', '.join(s.key_pressures)}")
        md.append(f"- Conflicts: {len(s.conflicts)} | Gaps: {len(s.evidence_gaps)}\n")

    md.append(f"\n_Disclaimer: {report.disclaimer}_")
    return "\n".join(md)
