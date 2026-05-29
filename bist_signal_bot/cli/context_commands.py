import argparse
import sys
from typing import Optional
from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.cli.formatting import print_output
from bist_signal_bot.context_fusion.reporting import (
    snapshot_to_dict, context_report_to_dict, format_context_snapshot_text,
    format_conflicts_text, format_evidence_gaps_text, format_research_graph_text
)

def handle_context_command(args: argparse.Namespace):
    from bist_signal_bot.app.context_fusion_app import create_context_fusion_engine

    settings = get_settings()
    engine = create_context_fusion_engine(settings)

    if args.ctx_command == "build":
        if args.signal_id:
            payload = {"signal_id": args.signal_id, "symbol": args.symbol or "UNKNOWN", "strategy_name": args.strategy_name}
            snap = engine.build_snapshot_for_signal(payload, save=args.save)
        else:
            if not args.symbol:
                print("Error: --symbol is required when not using --signal-id")
                sys.exit(1)
            snap = engine.build_snapshot_for_symbol(args.symbol, strategy_name=args.strategy_name, save=args.save)

        if args.json:
            print_output(snapshot_to_dict(snap), as_json=True)
        else:
            print_output(format_context_snapshot_text(snap), as_json=False)

    elif args.ctx_command == "show":
        if args.snapshot_id:
            snap = engine.store.get_snapshot(args.snapshot_id)
        else:
            if not args.symbol:
                print("Error: --symbol or --snapshot-id is required")
                sys.exit(1)
            snap = engine.store.load_latest_snapshot(args.symbol)

        if not snap:
            print("Snapshot not found.")
            sys.exit(1)

        if args.json:
            print_output(snapshot_to_dict(snap), as_json=True)
        else:
            print_output(format_context_snapshot_text(snap), as_json=False)

    elif args.ctx_command == "graph":
        if args.snapshot_id:
            snap = engine.store.get_snapshot(args.snapshot_id)
        else:
            if not args.symbol:
                print("Error: --symbol or --snapshot-id is required")
                sys.exit(1)
            snap = engine.store.load_latest_snapshot(args.symbol)

        if not snap or not snap.research_graph:
            print("Graph not found in snapshot.")
            sys.exit(1)

        if args.json:
            from bist_signal_bot.context_fusion.reporting import research_graph_to_dict
            print_output(research_graph_to_dict(snap.research_graph), as_json=True)
        else:
            print_output(format_research_graph_text(snap.research_graph), as_json=False)

    elif args.ctx_command == "conflicts":
        if args.latest:
            conflicts = engine.store.load_conflicts(symbol=args.symbol, limit=50)
        else:
            snap = engine.store.load_latest_snapshot(args.symbol) if args.symbol else None
            conflicts = snap.conflicts if snap else []

        if args.json:
            from bist_signal_bot.context_fusion.reporting import conflict_to_dict
            print_output([conflict_to_dict(c) for c in conflicts], as_json=True)
        else:
            print_output(format_conflicts_text(conflicts), as_json=False)

    elif args.ctx_command == "gaps":
        if args.latest:
            gaps = engine.store.load_gaps(symbol=args.symbol, limit=50)
        else:
            snap = engine.store.load_latest_snapshot(args.symbol) if args.symbol else None
            gaps = snap.evidence_gaps if snap else []

        if args.json:
            from bist_signal_bot.context_fusion.reporting import gap_to_dict
            print_output([gap_to_dict(g) for g in gaps], as_json=True)
        else:
            print_output(format_evidence_gaps_text(gaps), as_json=False)

    elif args.ctx_command == "score":
        if args.snapshot_id:
            snap = engine.store.get_snapshot(args.snapshot_id)
        else:
            if not args.symbol:
                print("Error: --symbol or --snapshot-id is required")
                sys.exit(1)
            snap = engine.store.load_latest_snapshot(args.symbol)

        if not snap or not snap.composite_score:
            print("Score not found.")
            sys.exit(1)

        if args.json:
            from bist_signal_bot.context_fusion.reporting import composite_score_to_dict
            print_output(composite_score_to_dict(snap.composite_score), as_json=True)
        else:
            print(f"Composite Score for {snap.symbol}: {snap.composite_score.adjusted_score:.2f} ({snap.composite_score.final_status.value})")

    elif args.ctx_command == "health":
        health = engine.context_health(symbol=args.symbol)
        print_output(health, as_json=args.json)

    elif args.ctx_command == "report":
        report = engine.build_report(symbols=args.symbols)
        if args.json:
            print_output(context_report_to_dict(report), as_json=True)
        else:
            from bist_signal_bot.context_fusion.reporting import format_context_fusion_report_markdown
            print(format_context_fusion_report_markdown(report))

    elif args.ctx_command == "recent":
        limit = getattr(args, 'limit', 10)
        snaps = engine.refresh_recent_context(limit=limit)
        if args.json:
            print_output([snapshot_to_dict(s) for s in snaps], as_json=True)
        else:
            for s in snaps:
                score = s.composite_score.adjusted_score if s.composite_score else 0.0
                print(f"[{s.as_of.isoformat()}] {s.symbol}: Score {score:.2f}")

    elif args.ctx_command == "config":
        data = {
            "ENABLE_CONTEXT_FUSION": getattr(settings, "ENABLE_CONTEXT_FUSION", True),
            "WEIGHTS": engine.weight_manager.default_weights()
        }
        # Mask secrets (though weights are not secrets)
        print_output(data, as_json=args.json)

def setup_context_parser(subparsers):
    parser = subparsers.add_parser("context", help="Context Fusion Commands")
    sub = parser.add_subparsers(dest="ctx_command", required=True)

    b = sub.add_parser("build", help="Build context snapshot")
    b.add_argument("--symbol", type=str, help="Symbol")
    b.add_argument("--strategy-name", type=str, help="Strategy name")
    b.add_argument("--signal-id", type=str, help="Signal ID")
    b.add_argument("--save", action="store_true", help="Save the snapshot")
    b.add_argument("--json", action="store_true", help="Output as JSON")

    s = sub.add_parser("show", help="Show context snapshot")
    s.add_argument("--symbol", type=str, help="Symbol")
    s.add_argument("--snapshot-id", type=str, help="Snapshot ID")
    s.add_argument("--json", action="store_true", help="Output as JSON")

    g = sub.add_parser("graph", help="Show research graph")
    g.add_argument("--symbol", type=str, help="Symbol")
    g.add_argument("--snapshot-id", type=str, help="Snapshot ID")
    g.add_argument("--json", action="store_true", help="Output as JSON")

    c = sub.add_parser("conflicts", help="Show context conflicts")
    c.add_argument("--symbol", type=str, help="Symbol")
    c.add_argument("--latest", action="store_true", help="Show latest conflicts globally or for symbol")
    c.add_argument("--json", action="store_true", help="Output as JSON")

    eg = sub.add_parser("gaps", help="Show evidence gaps")
    eg.add_argument("--symbol", type=str, help="Symbol")
    eg.add_argument("--latest", action="store_true", help="Show latest gaps globally or for symbol")
    eg.add_argument("--json", action="store_true", help="Output as JSON")

    sc = sub.add_parser("score", help="Show composite research score")
    sc.add_argument("--symbol", type=str, help="Symbol")
    sc.add_argument("--snapshot-id", type=str, help="Snapshot ID")
    sc.add_argument("--json", action="store_true", help="Output as JSON")

    h = sub.add_parser("health", help="Check context fusion health")
    h.add_argument("--symbol", type=str, help="Symbol")
    h.add_argument("--json", action="store_true", help="Output as JSON")

    r = sub.add_parser("report", help="Generate context fusion report")
    r.add_argument("--symbols", nargs="+", help="Symbols")
    r.add_argument("--json", action="store_true", help="Output as JSON")

    rec = sub.add_parser("recent", help="Show recent context snapshots")
    rec.add_argument("--limit", type=int, default=10, help="Limit")
    rec.add_argument("--json", action="store_true", help="Output as JSON")

    cfg = sub.add_parser("config", help="Show context fusion config")
    cfg.add_argument("--json", action="store_true", help="Output as JSON")
