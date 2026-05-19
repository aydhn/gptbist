import json
import logging
from bist_signal_bot.app.breadth_app import BreadthApp
from bist_signal_bot.config.settings import Settings

logger = logging.getLogger(__name__)

def handle_breadth_commands(args, settings: Settings):
    if not hasattr(args, "breadth_command") or not args.breadth_command:
        print("Usage: python -m bist_signal_bot breadth [snapshot|relative-strength|sector-rotation|rank|leaders|laggards|regime|recent|config]")
        return

    app = BreadthApp(settings=settings)

    symbols = getattr(args, "symbols", [])
    if getattr(args, "group", None):
        # mock group resolve
        symbols = symbols or ["ASELS", "THYAO", "GARAN"]

    if args.breadth_command == "snapshot":
        if not symbols:
            print("Error: Provide symbols or a group.")
            return
        res = app.generate_snapshot(
            symbols=symbols,
            universe_name=getattr(args, "group", "CUSTOM") or "CUSTOM",
            benchmark_symbol=getattr(args, "benchmark", None),
            source=getattr(args, "source", "local_file"),
            save_snapshot=getattr(args, "save", False)
        )
        if getattr(args, "json", False):
            print(json.dumps(res.summary(), indent=2))
        else:
            print("Snapshot generated:")
            print(f"Status: {res.snapshot.status.value}")
            print(f"Composite Score: {res.snapshot.composite_score:.2f}")

    elif args.breadth_command == "relative-strength":
        res = app.generate_snapshot(symbols=symbols, universe_name=getattr(args, "group", "CUSTOM") or "CUSTOM", save_snapshot=False)
        scores = res.relative_strength_scores
        top = getattr(args, "top", None)
        if top:
            scores = sorted(scores, key=lambda x: x.composite_score, reverse=True)[:top]
        if getattr(args, "json", False):
            print(json.dumps([s.model_dump(mode='json') for s in scores], indent=2))
        else:
            for s in scores:
                print(f"{s.symbol}: {s.composite_score:.2f}")

    elif args.breadth_command == "sector-rotation":
        res = app.generate_snapshot(symbols=symbols, universe_name=getattr(args, "group", "CUSTOM") or "CUSTOM", save_snapshot=False)
        scores = res.sector_rotation_scores
        top = getattr(args, "top", None)
        if top:
            scores = scores[:top]
        if getattr(args, "json", False):
            print(json.dumps([s.model_dump(mode='json') for s in scores], indent=2))
        else:
            for s in scores:
                print(f"{s.sector}: {s.rotation_status.value}")

    elif args.breadth_command == "rank":
        res = app.generate_snapshot(symbols=symbols, universe_name=getattr(args, "group", "CUSTOM") or "CUSTOM", save_snapshot=False)
        rank = res.cross_sectional_ranking
        top = getattr(args, "top", None)
        if top:
            rank = rank[:top]
        if getattr(args, "json", False):
            print(json.dumps([r.model_dump(mode='json') for r in rank], indent=2))
        else:
            for r in rank:
                print(f"{r.rank}. {r.symbol}: {r.composite_score:.2f}")

    elif args.breadth_command == "leaders":
        leaders = app.get_leaders(getattr(args, "top", 20))
        if getattr(args, "json", False):
            print(json.dumps(leaders, indent=2))
        else:
            for l in leaders:
                print(f"{l['rank']}. {l['symbol']}: {l['composite_score']:.2f}")

    elif args.breadth_command == "laggards":
        laggards = app.get_laggards(getattr(args, "bottom", 20))
        if getattr(args, "json", False):
            print(json.dumps(laggards, indent=2))
        else:
            for l in laggards:
                print(f"{l['rank']}. {l['symbol']}: {l['composite_score']:.2f}")

    elif args.breadth_command == "regime":
        res = app.generate_snapshot(symbols=symbols, universe_name=getattr(args, "group", "CUSTOM") or "CUSTOM", save_snapshot=False)
        if getattr(args, "json", False):
            print(json.dumps(res.regime.model_dump(mode='json') if res.regime else {}, indent=2))
        else:
            if res.regime:
                print(f"Regime Status: {res.regime.status.value}")
                print(f"Risk Modifier: {res.regime.risk_modifier}")

    elif args.breadth_command == "recent":
        limit = getattr(args, "limit", 10)
        recent = app.get_recent_snapshots(limit)
        if getattr(args, "json", False):
            print(json.dumps(recent, indent=2))
        else:
            for r in recent:
                print(f"{r['as_of_date']} - {r['universe_name']}: {r['status']}")

    elif args.breadth_command == "config":
        conf = {k: v for k, v in settings.model_dump().items() if "BREADTH" in k}
        if getattr(args, "json", False):
            print(json.dumps(conf, indent=2))
        else:
            for k, v in conf.items():
                print(f"{k}: {v}")
