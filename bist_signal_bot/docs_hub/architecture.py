import uuid
from datetime import datetime
from typing import Optional

from bist_signal_bot.docs_hub.models import (
    ArchitectureMap, ArchitectureNode, ArchitectureEdge, ArchitectureNodeType, DocsIndex
)

class ArchitectureMapBuilder:
    def build_map(self) -> ArchitectureMap:
        nodes = self.module_nodes() + self.cli_command_nodes() + self.store_nodes()
        edges = self.integration_edges(nodes)

        return ArchitectureMap(
            map_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            nodes=nodes,
            edges=edges,
            module_count=len(self.module_nodes()),
            command_count=len(self.cli_command_nodes()),
            doc_count=0
        )

    def module_nodes(self) -> list[ArchitectureNode]:
        modules = [
            ("scanner", "Signals Scanner"),
            ("signals", "Signal Engine"),
            ("context_fusion", "Context Fusion Engine"),
            ("portfolio_construction", "Portfolio Builder"),
            ("qa", "Quality Assurance"),
            ("ops", "Local Operations"),
            ("bootstrap", "Bootstrap & MVP"),
            ("cli_ux", "CLI UX"),
            ("docs_hub", "Documentation Hub")
        ]
        return [
            ArchitectureNode(
                node_id=f"mod_{m[0]}",
                node_type=ArchitectureNodeType.MODULE,
                label=m[1],
                module_name=m[0],
                description=f"Core module {m[0]}"
            ) for m in modules
        ]

    def cli_command_nodes(self) -> list[ArchitectureNode]:
        return [
            ArchitectureNode(
                node_id="cli_docs_hub",
                node_type=ArchitectureNodeType.CLI_COMMAND,
                label="docs-hub",
                description="CLI command for Documentation Hub"
            )
        ]

    def store_nodes(self) -> list[ArchitectureNode]:
        return [
            ArchitectureNode(
                node_id="store_docs",
                node_type=ArchitectureNodeType.STORE,
                label="Docs Store",
                description="Local storage for docs hub"
            )
        ]

    def doc_nodes(self, index: Optional[DocsIndex] = None) -> list[ArchitectureNode]:
        if not index: return []
        return [
            ArchitectureNode(
                node_id=f"doc_{p.page_id}",
                node_type=ArchitectureNodeType.DOC,
                label=p.title,
                description=p.summary
            ) for p in index.pages
        ]

    def integration_edges(self, nodes: list[ArchitectureNode]) -> list[ArchitectureEdge]:
        rels = [
            ("mod_scanner", "mod_signals", "depends_on"),
            ("mod_signals", "mod_context_fusion", "depends_on"),
            ("mod_qa", "mod_docs_hub", "validates"),
            ("mod_cli_ux", "mod_docs_hub", "integrates_with")
        ]
        edges = []
        node_ids = {n.node_id for n in nodes}
        for src, dst, rel in rels:
            if src in node_ids and dst in node_ids:
                edges.append(
                    ArchitectureEdge(
                        edge_id=str(uuid.uuid4()),
                        from_node_id=src,
                        to_node_id=dst,
                        relationship=rel,
                        description=f"{src} {rel} {dst}"
                    )
                )
        return edges

    def render_mermaid(self, amap: ArchitectureMap) -> str:
        lines = ["graph TD;"]
        for edge in amap.edges:
            lines.append(f"    {edge.from_node_id}-->|{edge.relationship}|{edge.to_node_id};")
        return "\n".join(lines)

    def render_markdown(self, amap: ArchitectureMap) -> str:
        lines = [
            f"# Architecture Map ({amap.created_at})",
            "",
            "## Modules",
        ]
        for node in [n for n in amap.nodes if n.node_type == ArchitectureNodeType.MODULE]:
            lines.append(f"- **{node.label}** ({node.module_name}): {node.description}")
        return "\n".join(lines)
