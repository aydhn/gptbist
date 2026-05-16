
import argparse
import json
from datetime import datetime
from ..config.settings import get_settings
from ..app.research_app import (
    create_research_ledger, create_signal_journal,
    create_research_comparator, create_attribution_engine,
    create_research_note_manager, create_research_lineage_resolver
)
from ..research.models import ResearchRunType, ResearchRunStatus, ResearchQuery, ResearchTag, ResearchSignalOutcome, AttributionGroupBy
from ..research.reporting import (
    format_ledger_summary_text, format_research_run_text, format_signal_journal_text,
    format_comparison_report_text, format_attribution_report_text, ledger_entries_to_dataframe
)
from ..research.events import ResearchEventBuilder

def cmd_research_log(args, settings):
    ledger = create_research_ledger(settings)
    builder = ResearchEventBuilder(settings)

    metrics = {}
    for m in (args.metric or []):
        if "=" in m:
            k, v = m.split("=", 1)
            try:
                metrics[k] = float(v)
            except:
                metrics[k] = v

    tags = [ResearchTag(tag=t) for t in (args.tag or [])]

    try:
        run_type = ResearchRunType(args.type)
    except ValueError:
        print(f"Invalid run type: {args.type}")
        return 1

    run = builder.generic_run(
        run_type=run_type,
        title=args.title,
        metrics=metrics,
        metadata={"body": args.body} if args.body else {}
    )
    if args.symbol: run.symbols.append(args.symbol)
    if args.strategy: run.strategy_name = args.strategy
    run.tags = tags

    entry = ledger.append_run(run, message=args.body or "Manual CLI log")
    if args.json:
        print(entry.model_dump_json(indent=2))
    else:
        print(f"Logged run {run.run_id} ({entry.entry_id})")
    return 0

def cmd_research_list(args, settings):
    ledger = create_research_ledger(settings)
    query_args = {"limit": args.limit}
    if args.type:
        try:
            query_args["run_types"] = [ResearchRunType(args.type)]
        except ValueError:
            print(f"Invalid run type: {args.type}")
            return 1
    if args.symbol: query_args["symbols"] = [args.symbol]
    if args.strategy: query_args["strategies"] = [args.strategy]
    if args.tag: query_args["tags"] = [args.tag]

    query = ResearchQuery(**query_args)
    entries = ledger.load_entries(limit=args.limit, query=query)

    if getattr(args, 'json', False):
        data = [e.model_dump() for e in entries]
        print(json.dumps(data, indent=2, default=str))
    else:
        print(format_ledger_summary_text(entries))
    return 0

def cmd_research_show(args, settings):
    ledger = create_research_ledger(settings)
    run = ledger.get_run(args.run_id)
    if not run:
        print(f"Run {args.run_id} not found.")
        return 1

    if getattr(args, 'json', False):
        print(run.model_dump_json(indent=2))
    else:
        print(format_research_run_text(run))
    return 0

def cmd_research_journal(args, settings):
    journal = create_signal_journal(settings)
    entries = journal.load_entries(limit=args.limit, symbol=args.symbol, strategy_name=args.strategy)

    if getattr(args, 'json', False):
        data = [e.model_dump() for e in entries]
        print(json.dumps(data, indent=2, default=str))
    else:
        print(format_signal_journal_text(entries))
    return 0

def cmd_research_outcome(args, settings):
    journal = create_signal_journal(settings)
    try:
        out_enum = ResearchSignalOutcome(args.outcome)
    except ValueError:
        print(f"Invalid outcome: {args.outcome}")
        return 1

    try:
        updated = journal.update_outcome(args.journal_id, out_enum, outcome_return_pct=args.return_pct, horizon_bars=args.horizon, confirm=args.confirm)
        print(f"Successfully updated outcome for {args.journal_id} to {out_enum.value}")
        return 0
    except Exception as e:
        print(f"Failed to update outcome: {e}")
        return 1

def cmd_research_compare(args, settings):
    comparator = create_research_comparator(settings)
    try:
        if getattr(args, 'runs', None):
            report = comparator.compare_runs(args.runs, args.metric)
        elif getattr(args, 'symbol', None) and getattr(args, 'strategies', None):
            report = comparator.compare_strategy(args.symbol, args.strategies, args.metric or settings.RESEARCH_DEFAULT_COMPARE_METRIC)
        elif getattr(args, 'type', None):
            rt = ResearchRunType(args.type)
            report = comparator.compare_recent(rt, args.limit, args.metric)
        else:
            print("Must provide --runs, or --type, or --symbol + --strategies")
            return 1

        if getattr(args, 'json', False):
            print(report.model_dump_json(indent=2))
        else:
            print(format_comparison_report_text(report))
        return 0
    except Exception as e:
        print(f"Comparison failed: {e}")
        return 1

def cmd_research_attribution(args, settings):
    engine = create_attribution_engine(settings)
    try:
        gb = AttributionGroupBy(args.group_by)
    except ValueError:
        print(f"Invalid group_by: {args.group_by}")
        return 1

    try:
        entries = engine.journal.load_entries(limit=5000)
        report = engine.build_attribution_from_journal(entries, gb)
        if getattr(args, 'json', False):
            print(report.model_dump_json(indent=2))
        else:
            print(format_attribution_report_text(report))
        return 0
    except Exception as e:
        print(f"Attribution failed: {e}")
        return 1

def cmd_research_note(args, settings):
    manager = create_research_note_manager(settings)

    if getattr(args, 'list', False):
        notes = manager.list_notes()
        for n in notes:
            print(f"{n.note_id} | {n.title}")
    elif getattr(args, 'show', None):
        note = manager.show_note(args.show)
        if note:
            print(note.model_dump_json(indent=2))
        else:
            print(f"Note {args.show} not found")
            return 1
    elif getattr(args, 'delete', None):
        try:
            manager.delete_note(args.delete, confirm=args.confirm)
            print(f"Deleted note {args.delete}")
        except Exception as e:
            print(f"Failed to delete note: {e}")
            return 1
    elif getattr(args, 'title', None) and getattr(args, 'body', None):
        try:
            note = manager.add_note(args.title, args.body, tags=args.tag)
            print(f"Added note {note.note_id}")
        except Exception as e:
             print(f"Failed to add note: {e}")
             return 1
    else:
        print("Provide --title/--body, --list, --show, or --delete")
        return 1
    return 0

def cmd_research_lineage(args, settings):
    resolver = create_research_lineage_resolver(settings)
    summary = resolver.lineage_summary(args.run_id)
    if getattr(args, 'json', False):
        print(json.dumps(summary, indent=2))
    else:
        print(f"Lineage for {args.run_id}: Parents: {summary['parents_count']}, Children: {summary['children_count']}")
    return 0

def cmd_research_export(args, settings):
    ledger = create_research_ledger(settings)
    entries = ledger.load_entries(limit=1000)

    if args.format == "json":
        data = [e.model_dump() for e in entries]
        print(json.dumps(data, indent=2, default=str))
    elif args.format == "csv":
        df = ledger_entries_to_dataframe(entries)
        print(df.to_csv(index=False))
    elif args.format == "markdown":
        print(format_ledger_summary_text(entries))
    return 0

def cmd_research_recent(args, settings):
    ledger = create_research_ledger(settings)
    entries = ledger.load_entries(limit=args.limit)
    if getattr(args, 'json', False):
        data = [e.model_dump() for e in entries]
        print(json.dumps(data, indent=2, default=str))
    else:
        print(format_ledger_summary_text(entries))
    return 0

def cmd_research_config(args, settings):
    configs = {k: v for k, v in settings.model_dump().items() if k.startswith("RESEARCH_")}
    if getattr(args, 'json', False):
        print(json.dumps(configs, indent=2))
    else:
        for k, v in configs.items():
            print(f"{k} = {v}")
    return 0

def handle_research_commands(args, settings):
    import argparse
    parser = argparse.ArgumentParser(prog="research")
    subparsers = parser.add_subparsers(dest="research_cmd")

    log_p = subparsers.add_parser("log")
    log_p.add_argument("--type", required=True)
    log_p.add_argument("--title", required=True)
    log_p.add_argument("--symbol")
    log_p.add_argument("--strategy")
    log_p.add_argument("--tag", action="append")
    log_p.add_argument("--metric", action="append")
    log_p.add_argument("--body")
    log_p.add_argument("--json", action="store_true")

    list_p = subparsers.add_parser("list")
    list_p.add_argument("--type")
    list_p.add_argument("--symbol")
    list_p.add_argument("--strategy")
    list_p.add_argument("--tag")
    list_p.add_argument("--limit", type=int, default=20)
    list_p.add_argument("--json", action="store_true")

    show_p = subparsers.add_parser("show")
    show_p.add_argument("run_id")
    show_p.add_argument("--json", action="store_true")

    journal_p = subparsers.add_parser("journal")
    journal_p.add_argument("--symbol")
    journal_p.add_argument("--strategy")
    journal_p.add_argument("--limit", type=int, default=50)
    journal_p.add_argument("--json", action="store_true")

    outcome_p = subparsers.add_parser("outcome")
    outcome_p.add_argument("journal_id")
    outcome_p.add_argument("--outcome", required=True)
    outcome_p.add_argument("--return-pct", type=float)
    outcome_p.add_argument("--horizon", type=int)
    outcome_p.add_argument("--confirm", action="store_true")

    compare_p = subparsers.add_parser("compare")
    compare_p.add_argument("--runs", nargs="+")
    compare_p.add_argument("--type")
    compare_p.add_argument("--symbol")
    compare_p.add_argument("--strategies", nargs="+")
    compare_p.add_argument("--metric")
    compare_p.add_argument("--limit", type=int, default=10)
    compare_p.add_argument("--json", action="store_true")

    attr_p = subparsers.add_parser("attribution")
    attr_p.add_argument("--group-by", required=True)
    attr_p.add_argument("--json", action="store_true")

    note_p = subparsers.add_parser("note")
    note_p.add_argument("--title")
    note_p.add_argument("--body")
    note_p.add_argument("--tag", action="append")
    note_p.add_argument("--list", action="store_true")
    note_p.add_argument("--show")
    note_p.add_argument("--delete")
    note_p.add_argument("--confirm", action="store_true")

    lineage_p = subparsers.add_parser("lineage")
    lineage_p.add_argument("run_id")
    lineage_p.add_argument("--json", action="store_true")

    export_p = subparsers.add_parser("export")
    export_p.add_argument("--format", required=True, choices=["csv", "json", "markdown"])
    export_p.add_argument("--json", action="store_true")

    recent_p = subparsers.add_parser("recent")
    recent_p.add_argument("--limit", type=int, default=10)
    recent_p.add_argument("--json", action="store_true")

    config_p = subparsers.add_parser("config")
    config_p.add_argument("--json", action="store_true")

    parsed = parser.parse_args(args.args)
    if parsed.research_cmd == "log": return cmd_research_log(parsed, settings)
    if parsed.research_cmd == "list": return cmd_research_list(parsed, settings)
    if parsed.research_cmd == "show": return cmd_research_show(parsed, settings)
    if parsed.research_cmd == "journal": return cmd_research_journal(parsed, settings)
    if parsed.research_cmd == "outcome": return cmd_research_outcome(parsed, settings)
    if parsed.research_cmd == "compare": return cmd_research_compare(parsed, settings)
    if parsed.research_cmd == "attribution": return cmd_research_attribution(parsed, settings)
    if parsed.research_cmd == "note": return cmd_research_note(parsed, settings)
    if parsed.research_cmd == "lineage": return cmd_research_lineage(parsed, settings)
    if parsed.research_cmd == "export": return cmd_research_export(parsed, settings)
    if parsed.research_cmd == "recent": return cmd_research_recent(parsed, settings)
    if parsed.research_cmd == "config": return cmd_research_config(parsed, settings)
    parser.print_help()
    return 1
