import uuid
from datetime import datetime, timezone
from typing import List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ResearchGraph, ResearchGraphNode, ResearchGraphNodeType,
    ResearchGraphEdge, ContextLayerSummary, ContextSignal
)

class ResearchGraphBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def build_graph(self, symbol: str, signal_id: Optional[str], summaries: List[ContextLayerSummary], signals: List[ContextSignal]) -> ResearchGraph:
        nodes = []
        edges = []

        sym_node = self.node_for_symbol(symbol)
        nodes.append(sym_node)

        sig_node = self.node_for_signal(signal_id)
        if sig_node:
            nodes.append(sig_node)
            edges.append(ResearchGraphEdge(
                edge_id=f"e_{sym_node.node_id}_{sig_node.node_id}",
                from_node_id=sig_node.node_id,
                to_node_id=sym_node.node_id,
                relationship="TARGETS_SYMBOL",
                message="Signal is for symbol"
            ))

        context_nodes = self.nodes_for_context_signals(signals)
        nodes.extend(context_nodes)

        c_edges = self.edges_for_context(sym_node, context_nodes, signals)
        edges.extend(c_edges)

        nodes = self.deduplicate_nodes(nodes)
        edges = self.deduplicate_edges(edges)

        return ResearchGraph(
            graph_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            symbol=symbol,
            signal_id=signal_id,
            nodes=nodes,
            edges=edges
        )

    def node_for_symbol(self, symbol: str) -> ResearchGraphNode:
        return ResearchGraphNode(
            node_id=f"sym_{symbol}",
            node_type=ResearchGraphNodeType.SYMBOL,
            label=f"Symbol: {symbol}",
            symbol=symbol
        )

    def node_for_signal(self, signal_id: Optional[str]) -> Optional[ResearchGraphNode]:
        if not signal_id:
            return None
        return ResearchGraphNode(
            node_id=f"sig_{signal_id}",
            node_type=ResearchGraphNodeType.SIGNAL,
            label=f"Signal: {signal_id}",
            object_id=signal_id
        )

    def nodes_for_context_signals(self, signals: List[ContextSignal]) -> List[ResearchGraphNode]:
        nodes = []
        for s in signals:
            nodes.append(ResearchGraphNode(
                node_id=f"ctx_{s.context_id}",
                node_type=ResearchGraphNodeType.CONTEXT_LAYER,
                label=f"[{s.layer.value}] {s.title}",
                object_id=s.context_id,
                symbol=s.symbol,
                metadata={"status": s.status.value, "direction": s.direction.value, "score": s.normalized_score}
            ))
        return nodes

    def edges_for_context(self, symbol_node: ResearchGraphNode, context_nodes: List[ResearchGraphNode], signals: List[ContextSignal]) -> List[ResearchGraphEdge]:
        edges = []
        for node in context_nodes:
            edges.append(ResearchGraphEdge(
                edge_id=f"e_{node.node_id}_{symbol_node.node_id}",
                from_node_id=node.node_id,
                to_node_id=symbol_node.node_id,
                relationship="PROVIDES_CONTEXT",
                message="Provides context for symbol"
            ))
        return edges

    def deduplicate_nodes(self, nodes: List[ResearchGraphNode]) -> List[ResearchGraphNode]:
        seen = set()
        unique = []
        for n in nodes:
            if n.node_id not in seen:
                seen.add(n.node_id)
                unique.append(n)
        return unique

    def deduplicate_edges(self, edges: List[ResearchGraphEdge]) -> List[ResearchGraphEdge]:
        seen = set()
        unique = []
        for e in edges:
            if e.edge_id not in seen:
                seen.add(e.edge_id)
                unique.append(e)
        return unique
