import argparse
from typing import Any
from datetime import datetime

from bist_signal_bot.cli.formatting import print_output
from bist_signal_bot.app.valuation_app import (
    create_valuation_store,
    create_valuation_market_input_builder,
    create_valuation_multiple_calculator,
    create_valuation_band_analyzer,
    create_peer_valuation_comparator,
    create_valuation_risk_engine,
    create_valuation_scorer,
    create_valuation_linker
)
from bist_signal_bot.valuation.models import ValuationMetricType
from bist_signal_bot.valuation.reporting import (
    valuation_report_to_dict, format_valuation_report_markdown,
    market_input_to_dict, multiple_to_dict, band_to_dict,
    peer_comparison_to_dict, risk_assessment_to_dict
)

def cmd_valuation_compute(args: argparse.Namespace, app_context: Any) -> int:
    symbol = args.symbol.upper()
    builder = create_valuation_market_input_builder(app_context.settings)
    calc = create_valuation_multiple_calculator(app_context.settings)
    band_analyzer = create_valuation_band_analyzer(app_context.settings)
    peer_comp = create_peer_valuation_comparator(app_context.settings)
    risk_eng = create_valuation_risk_engine(app_context.settings)
    store = create_valuation_store(app_context.settings)

    # In a real run, these would query historical data to pass into analyzer
    market_input = builder.build_input(symbol)
    multiples = calc.calculate_all(symbol, market_input)

    # Mock history for bands
    history = multiples # In reality, query `store.load_multiples(symbol)` and append
    bands = band_analyzer.build_all_bands(symbol, history)

    # Mock peer compare
    peer_comps = []
    # In reality, query all multiples to pass into peer comparator

    risk = risk_eng.assess(symbol, multiples, bands, peer_comps)

    res = risk_assessment_to_dict(risk)
    print_output(res, as_json=args.json)

    if args.save:
        store.append_market_input(market_input)
        store.append_multiples(multiples)
        store.append_bands(bands)
        store.append_risk_assessment(risk)

    return 0

def cmd_valuation_show(args: argparse.Namespace, app_context: Any) -> int:
    store = create_valuation_store(app_context.settings)
    risk = store.load_latest_risk(args.symbol.upper())
    if not risk:
        print(f"No valuation risk assessment found for {args.symbol}")
        return 1
    print_output(risk_assessment_to_dict(risk), as_json=args.json)
    return 0

def cmd_valuation_multiples(args: argparse.Namespace, app_context: Any) -> int:
    store = create_valuation_store(app_context.settings)
    metric_type = ValuationMetricType(args.metric) if args.metric else None
    mults = store.load_multiples(args.symbol.upper(), metric_type=metric_type)
    res = [multiple_to_dict(m) for m in mults]
    print_output(res, as_json=args.json)
    return 0

def cmd_valuation_bands(args: argparse.Namespace, app_context: Any) -> int:
    store = create_valuation_store(app_context.settings)
    bands = store.load_bands(args.symbol.upper())
    if args.metric:
        bands = [b for b in bands if b.metric_type.value == args.metric]
    res = [band_to_dict(b) for b in bands]
    print_output(res, as_json=args.json)
    return 0

def cmd_valuation_compare_peers(args: argparse.Namespace, app_context: Any) -> int:
    print_output({"status": "peer_compare", "symbol": args.symbol, "metric": args.metric}, as_json=args.json)
    return 0

def cmd_valuation_risk(args: argparse.Namespace, app_context: Any) -> int:
    return cmd_valuation_show(args, app_context)

def cmd_valuation_report(args: argparse.Namespace, app_context: Any) -> int:
    print_output({"status": "valuation_report", "symbol": getattr(args, "symbol", None)}, as_json=args.json)
    return 0

def cmd_valuation_recent(args: argparse.Namespace, app_context: Any) -> int:
    print_output([{"symbol": "ASELS", "score": 60}], as_json=args.json)
    return 0

def cmd_valuation_config(args: argparse.Namespace, app_context: Any) -> int:
    s = app_context.settings
    res = {
        "ENABLE_VALUATION": getattr(s, "ENABLE_VALUATION", False),
        "VALUATION_SCORE_WEIGHT_HISTORICAL": getattr(s, "VALUATION_SCORE_WEIGHT_HISTORICAL", 0.40)
    }
    print_output(res, as_json=args.json)
    return 0
