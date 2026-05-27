import argparse
from pathlib import Path
from datetime import datetime

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.app.events_app import (
    create_event_importer, create_event_calendar, create_event_window_builder,
    create_event_risk_engine, create_blackout_policy_manager, create_event_store
)
from bist_signal_bot.events.reporting import format_event_calendar_report_markdown
from bist_signal_bot.events.models import MarketEventType
import json

def register_event_calendar_commands(subparsers):
    parser = subparsers.add_parser('event-calendar', help='Manage the Event Risk Calendar')
    cmds = parser.add_subparsers(dest='event_cmd', required=True)

    # import
    import_cmd = cmds.add_parser('import', help='Import market events from file')
    import_cmd.add_argument('--file', type=str, required=True, help='Path to CSV or JSON file')
    import_cmd.add_argument('--dry-run', action='store_true', help='Validate without saving')
    import_cmd.add_argument('--confirm', action='store_true', help='Confirm the import')

    # list
    list_cmd = cmds.add_parser('list', help='List events')
    list_cmd.add_argument('--symbol', type=str, help='Filter by symbol')
    list_cmd.add_argument('--type', type=str, help='Filter by event type')
    list_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # show
    show_cmd = cmds.add_parser('show', help='Show event details')
    show_cmd.add_argument('event_id', type=str, help='Event ID')
    show_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # upcoming
    upcoming_cmd = cmds.add_parser('upcoming', help='List upcoming events')
    upcoming_cmd.add_argument('--days', type=int, default=30, help='Days to look ahead')
    upcoming_cmd.add_argument('--symbol', type=str, help='Filter by symbol')
    upcoming_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # windows
    windows_cmd = cmds.add_parser('windows', help='List active event windows')
    windows_cmd.add_argument('--symbol', type=str, help='Filter by symbol')
    windows_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # check
    check_cmd = cmds.add_parser('check', help='Check event risk for a symbol')
    check_cmd.add_argument('symbol', type=str, help='Symbol to check')
    check_cmd.add_argument('--strategy', type=str, help='Strategy name context')
    check_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # portfolio-check
    pcheck_cmd = cmds.add_parser('portfolio-check', help='Check event risk for a portfolio')
    pcheck_cmd.add_argument('--symbols', nargs='+', help='Symbols to check')
    pcheck_cmd.add_argument('--portfolio-id', type=str, help='Portfolio ID to check')
    pcheck_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # policies
    policies_cmd = cmds.add_parser('policies', help='List blackout policies')
    policies_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # snapshot
    snapshot_cmd = cmds.add_parser('snapshot', help='Create a calendar snapshot')
    snapshot_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # report
    report_cmd = cmds.add_parser('report', help='Generate event calendar report')
    report_cmd.add_argument('--latest', action='store_true', help='Show latest report')
    report_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # recent
    recent_cmd = cmds.add_parser('recent', help='List recent imports/reports')
    recent_cmd.add_argument('--limit', type=int, default=10, help='Number of items to show')
    recent_cmd.add_argument('--json', action='store_true', help='Output JSON')

    # config
    config_cmd = cmds.add_parser('config', help='Show event calendar config')
    config_cmd.add_argument('--json', action='store_true', help='Output JSON')


def handle_event_calendar_command(args):
    settings = get_settings()

    if args.event_cmd == 'import':
        importer = create_event_importer(settings)
        result = importer.import_file(Path(args.file), confirm=args.confirm and not args.dry_run)
        print(f"Import {result.import_id} complete. Imported: {result.events_imported}, Skipped: {result.events_skipped}")

    elif args.event_cmd == 'list':
        calendar = create_event_calendar(settings)
        ev_type = MarketEventType(args.type) if args.type else None
        events = calendar.list_events(symbol=args.symbol, event_type=ev_type)
        if args.json:
            print(json.dumps([e.model_dump(mode='json') for e in events], indent=2))
        else:
            for ev in events:
                print(f"{ev.event_date.strftime('%Y-%m-%d')} | {ev.symbol or 'MARKET'} | {ev.event_type.value} | {ev.title}")

    elif args.event_cmd == 'show':
        calendar = create_event_calendar(settings)
        ev = calendar.get_event(args.event_id)
        if not ev:
            print("Event not found")
            return
        if args.json:
            print(ev.model_dump_json(indent=2))
        else:
            print(f"Event: {ev.title}")
            print(f"Type: {ev.event_type.value}")
            print(f"Date: {ev.event_date}")
            print(f"Status: {ev.status.value}")

    elif args.event_cmd == 'upcoming':
        calendar = create_event_calendar(settings)
        events = calendar.upcoming_events(days=args.days, symbol=args.symbol)
        if args.json:
            print(json.dumps([e.model_dump(mode='json') for e in events], indent=2))
        else:
            for ev in events:
                print(f"{ev.event_date.strftime('%Y-%m-%d')} | {ev.symbol or 'MARKET'} | {ev.title}")

    elif args.event_cmd == 'windows':
        calendar = create_event_calendar(settings)
        window_builder = create_event_window_builder(settings)
        now = datetime.now()
        events = calendar.upcoming_events(days=30)
        windows = window_builder.build_windows(events)
        active = window_builder.active_windows(now, windows, symbol=args.symbol)
        if args.json:
            print(json.dumps([w.model_dump(mode='json') for w in active], indent=2))
        else:
            for w in active:
                print(f"{w.starts_at.strftime('%Y-%m-%d')} to {w.ends_at.strftime('%Y-%m-%d')} | {w.window_type.value} | {w.decision.value}")

    elif args.event_cmd == 'check':
        engine = create_event_risk_engine(settings)
        assessment = engine.assess_symbol(args.symbol, strategy_name=args.strategy)
        if args.json:
            print(assessment.model_dump_json(indent=2))
        else:
            from bist_signal_bot.notifications.formatter import format_event_risk_assessment
            print(format_event_risk_assessment(assessment))

    elif args.event_cmd == 'portfolio-check':
        engine = create_event_risk_engine(settings)
        symbols = args.symbols or []
        assessments = engine.assess_portfolio(symbols)
        if args.json:
            print(json.dumps({s: a.model_dump(mode='json') for s, a in assessments.items()}, indent=2))
        else:
            for s, a in assessments.items():
                print(f"{s}: Score {a.risk_score} -> {a.decision.value}")

    elif args.event_cmd == 'policies':
        manager = create_blackout_policy_manager(settings)
        policies = manager.default_policies()
        if args.json:
            print(json.dumps([p.model_dump(mode='json') for p in policies], indent=2))
        else:
            for p in policies:
                print(f"{p.name} | {p.decision.value} | Pre:{p.pre_event_days} Post:{p.post_event_days}")

    elif args.event_cmd == 'snapshot':
        calendar = create_event_calendar(settings)
        snapshot = calendar.snapshot()
        if args.json:
            print(snapshot.model_dump_json(indent=2))
        else:
            from bist_signal_bot.notifications.formatter import format_event_calendar_snapshot
            print(format_event_calendar_snapshot(snapshot))

    elif args.event_cmd == 'report':
        calendar = create_event_calendar(settings)
        engine = create_event_risk_engine(settings)
        snapshot = calendar.snapshot()
        upcoming = calendar.upcoming_events(days=7)
        assessments = []
        if upcoming:
            symbols = [e.symbol for e in upcoming if e.symbol]
            assessments = list(engine.assess_portfolio(list(set(symbols))).values())

        md = format_event_calendar_report_markdown(snapshot, upcoming, assessments)
        if args.json:
            print(json.dumps({"report": md}))
        else:
            print(md)

    elif args.event_cmd == 'recent':
        store = create_event_store(settings)
        events = store.load_events(limit=args.limit)
        if args.json:
            print(json.dumps([e.model_dump(mode='json') for e in events], indent=2))
        else:
            print(f"Loaded {len(events)} recent events")
            for ev in events[-args.limit:]:
                print(f"{ev.event_date.strftime('%Y-%m-%d')} | {ev.title}")

    elif args.event_cmd == 'config':
        conf = {k: v for k, v in settings.model_dump().items() if 'EVENT' in k}
        if args.json:
            print(json.dumps(conf, indent=2))
        else:
            for k, v in conf.items():
                print(f"{k}: {v}")
