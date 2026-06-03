import argparse
import json
from datetime import datetime
import uuid
from pathlib import Path

from bist_signal_bot.app.markets_app import (
    create_market_registry, create_instrument_registry, create_symbol_normalizer,
    create_market_calendar_provider, create_market_session_provider,
    create_market_universe_builder, create_market_validation_engine,
    create_market_governance_engine
)
from bist_signal_bot.markets.reporting import (
    market_to_dict, instrument_to_dict, format_market_text, format_instrument_text,
    format_market_registry_report_markdown, report_to_dict, universe_to_dict
)
from bist_signal_bot.markets.models import MarketRegistryReport

def add_market_registry_parser(subparsers):
    parser = subparsers.add_parser("market-registry", help="Multi-market research metadata and instrument registry")
    sp = parser.add_subparsers(dest="market_cmd")

    p_list = sp.add_parser("list", help="List available markets")
    p_list.add_argument("--json", action="store_true")

    p_show = sp.add_parser("show", help="Show market details")
    p_show.add_argument("market_id_or_name", help="Market ID or name")
    p_show.add_argument("--json", action="store_true")

    p_inst = sp.add_parser("instruments", help="List instruments for market")
    p_inst.add_argument("--market-id", required=True)
    p_inst.add_argument("--json", action="store_true")

    p_norm = sp.add_parser("normalize-symbols", help="Normalize raw symbols")
    p_norm.add_argument("symbols", nargs="+")
    p_norm.add_argument("--market-id", required=True)
    p_norm.add_argument("--json", action="store_true")

    p_cal = sp.add_parser("calendar", help="Get market calendar")
    p_cal.add_argument("--market-id", required=True)
    p_cal.add_argument("--start", required=True)
    p_cal.add_argument("--end", required=True)
    p_cal.add_argument("--json", action="store_true")

    p_ses = sp.add_parser("sessions", help="Get market sessions")
    p_ses.add_argument("--market-id", required=True)
    p_ses.add_argument("--date", required=True)
    p_ses.add_argument("--json", action="store_true")

    p_univ = sp.add_parser("universe", help="Get market universe")
    p_univ.add_argument("--market-id")
    p_univ.add_argument("--name")
    p_univ.add_argument("--json", action="store_true")

    p_val = sp.add_parser("validate", help="Validate market instruments")
    p_val.add_argument("--market-id", required=True)
    p_val.add_argument("--symbols", nargs="*")
    p_val.add_argument("--json", action="store_true")

    p_gov = sp.add_parser("governance", help="Assess market governance")
    p_gov.add_argument("--market-id", required=True)
    p_gov.add_argument("--json", action="store_true")

    p_rep = sp.add_parser("report", help="Generate market registry report")
    p_rep.add_argument("--latest", action="store_true")
    p_rep.add_argument("--json", action="store_true")

    p_rec = sp.add_parser("recent", help="Show recent market operations")
    p_rec.add_argument("--limit", type=int, default=10)
    p_rec.add_argument("--json", action="store_true")

    p_cfg = sp.add_parser("config", help="Show market registry configuration")
    p_cfg.add_argument("--json", action="store_true")

def handle_market_registry(args):
    try:
        from bist_signal_bot.config.settings import ENABLE_MARKETS
    except ImportError:
        pass

    if args.market_cmd == "list":
        reg = create_market_registry()
        res = reg.list_markets()
        if args.json:
            print(json.dumps([market_to_dict(m) for m in res], indent=2))
        else:
            for m in res:
                print(format_market_text(m))

    elif args.market_cmd == "show":
        reg = create_market_registry()
        m = reg.get_market(args.market_id_or_name)
        if not m:
            print(f"Market {args.market_id_or_name} not found")
            return
        if args.json:
            print(json.dumps(market_to_dict(m), indent=2))
        else:
            print(format_market_text(m))

    elif args.market_cmd == "instruments":
        reg = create_instrument_registry()
        res = reg.list_instruments(args.market_id)
        if args.json:
            print(json.dumps([instrument_to_dict(i) for i in res], indent=2))
        else:
            for i in res:
                print(format_instrument_text(i))

    elif args.market_cmd == "normalize-symbols":
        norm = create_symbol_normalizer()
        res = norm.normalize_many(args.symbols, args.market_id)
        out = [{"raw": r.raw_symbol, "canonical": r.canonical_symbol, "market": r.market_id, "warnings": r.warnings} for r in res]
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            for o in out:
                print(f"{o['raw']} -> {o['canonical']} ({o['market']})")

    elif args.market_cmd == "calendar":
        cal = create_market_calendar_provider()
        res = cal.default_calendar(args.market_id, args.start, args.end)
        out = [{"date": r.date, "status": r.session_status.value} for r in res]
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            for o in out:
                print(f"{o['date']}: {o['status']}")

    elif args.market_cmd == "sessions":
        ses = create_market_session_provider()
        res = ses.default_sessions(args.market_id, args.date)
        out = [{"name": r.session_name, "status": r.status.value} for r in res]
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            for o in out:
                print(f"{o['name']}: {o['status']}")

    elif args.market_cmd == "universe":
        bld = create_market_universe_builder()
        if args.name:
            u = bld.build_universe(args.name, args.market_id or "UNKNOWN", [])
        else:
            u = bld.universe_for_market(args.market_id)
        if args.json:
            print(json.dumps(universe_to_dict(u), indent=2))
        else:
            print(f"Universe: {u.name} ({len(u.symbols)} symbols)")

    elif args.market_cmd == "validate":
        val = create_market_validation_engine()
        rows = [{"symbol": s} for s in (args.symbols or [])]
        res = val.validate_market_dataset(rows, args.market_id)
        if args.json:
            import json as j
            print(j.loads(res.model_dump_json()))
        else:
            print(f"Status: {res.status.value}")
            for f in res.findings:
                print(f"- {f}")

    elif args.market_cmd == "governance":
        gov = create_market_governance_engine()
        res = gov.assess_market(args.market_id)
        if args.json:
            import json as j
            print(j.loads(res.model_dump_json()))
        else:
            print(f"Status: {res.status.value}")
            print(f"Registry Complete: {res.registry_complete}")
            print(f"Instruments Available: {res.instruments_available}")

    elif args.market_cmd == "report":
        reg = create_market_registry()
        gov = create_market_governance_engine()
        bld = create_market_universe_builder()

        rep = MarketRegistryReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            markets=reg.list_markets(),
            instruments=[],
            universes=bld.default_universes(),
            calendars=[],
            validations=[],
            governance_assessments=[gov.assess_market("BIST_EQUITY"), gov.assess_market("US_EQUITY_RESEARCH")],
            key_findings=["Multi-market abstraction operational"]
        )

        if args.json:
            print(json.dumps(report_to_dict(rep), indent=2))
        else:
            print(format_market_registry_report_markdown(rep))

    elif args.market_cmd in ["recent", "config"]:
        out = {"status": "ok", "message": f"{args.market_cmd} executed (offline placeholder)", "disclaimer": "Local metadata only"}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(out["message"])
