import sys
import argparse
import json
from pathlib import Path

from bist_signal_bot.explainability.models import SignalExplanation, EvidenceCard, DecisionTrace
from bist_signal_bot.app.explainability_app import create_explainability_store, create_evidence_card_builder

def setup_parser(subparsers):
    parser = subparsers.add_parser("explain", help="Explainability commands")
    subcmds = parser.add_subparsers(dest="explain_cmd", help="Explain subcommands")

    signal_parser = subcmds.add_parser("signal", help="Explain a signal")
    signal_parser.add_argument("--symbol", type=str)
    signal_parser.add_argument("--strategy", type=str)
    signal_parser.add_argument("--signal-id", type=str)
    signal_parser.add_argument("--json", action="store_true")

    strategy_parser = subcmds.add_parser("strategy", help="Explain a strategy")
    strategy_parser.add_argument("strategy_name", type=str)
    strategy_parser.add_argument("--symbol", type=str)
    strategy_parser.add_argument("--json", action="store_true")

    ensemble_parser = subcmds.add_parser("ensemble", help="Explain an ensemble")
    ensemble_parser.add_argument("--symbol", type=str)
    ensemble_parser.add_argument("--json", action="store_true")

    trace_parser = subcmds.add_parser("trace", help="Explain a decision trace")
    trace_parser.add_argument("--symbol", type=str)
    trace_parser.add_argument("--strategy", type=str)
    trace_parser.add_argument("--trace-id", type=str)
    trace_parser.add_argument("--json", action="store_true")

    card_parser = subcmds.add_parser("card", help="Explain an evidence card")
    card_parser.add_argument("--symbol", type=str)
    card_parser.add_argument("--strategy", type=str)
    card_parser.add_argument("--signal-id", type=str)
    card_parser.add_argument("--card-id", type=str)
    card_parser.add_argument("--save", action="store_true")
    card_parser.add_argument("--json", action="store_true")

    recent_parser = subcmds.add_parser("recent", help="Explain recent signals")
    recent_parser.add_argument("--symbol", type=str)
    recent_parser.add_argument("--json", action="store_true")

    report_parser = subcmds.add_parser("report", help="Explain report")
    report_parser.add_argument("--latest", action="store_true")
    report_parser.add_argument("--json", action="store_true")

    config_parser = subcmds.add_parser("config", help="Explain config")
    config_parser.add_argument("--json", action="store_true")


def handle_explain(args):
    cmd = args.explain_cmd
    store = create_explainability_store()

    if cmd == "signal":
        print(f"Explain signal mock for symbol={args.symbol}, strategy={args.strategy}")
    elif cmd == "strategy":
        print(f"Explain strategy mock for {args.strategy_name}, symbol={args.symbol}")
    elif cmd == "ensemble":
        print(f"Explain ensemble mock for symbol={args.symbol}")
    elif cmd == "trace":
        print(f"Explain trace mock for symbol={args.symbol}, trace_id={args.trace_id}")
    elif cmd == "card":
        print(f"Explain card mock for symbol={args.symbol}, card_id={args.card_id}")
    elif cmd == "recent":
        print(f"Explain recent mock for symbol={args.symbol}")
    elif cmd == "report":
        print("Explain report mock")
    elif cmd == "config":
        print("Explain config mock")
    else:
        print("Invalid command")
