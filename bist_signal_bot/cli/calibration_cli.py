import argparse
import json
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.calibration_app import (
    create_calibration_store, create_outcome_dataset_builder,
    create_calibration_bin_builder, create_signal_calibrator,
    create_threshold_tuner, create_outcome_cohort_analyzer,
    create_error_taxonomy_builder, create_calibration_scorer
)
from bist_signal_bot.calibration.models import CalibrationScoreType, OutcomeHorizon
from bist_signal_bot.calibration.reporting import (
    calibration_result_to_dict, reliability_curve_to_dict, threshold_result_to_dict,
    cohort_to_dict, error_case_to_dict, calibration_report_to_dict,
    format_calibration_result_text, format_threshold_result_text, format_cohorts_text, format_error_cases_text,
    format_calibration_report_markdown
)
import logging

logger = logging.getLogger(__name__)

def setup_calibration_parser(subparsers):
    parser = subparsers.add_parser("calibration", help="Signal Calibration and Outcome Analytics")
    sub = parser.add_subparsers(dest="calib_cmd")

    b_out = sub.add_parser("build-outcomes", help="Build outcome dataset")
    b_out.add_argument("--strategy", type=str)
    b_out.add_argument("--symbol", type=str)
    b_out.add_argument("--json", action="store_true")

    ev = sub.add_parser("evaluate", help="Evaluate calibration")
    ev.add_argument("--score-type", type=str, required=True)
    ev.add_argument("--strategy", type=str)
    ev.add_argument("--json", action="store_true")

    fit = sub.add_parser("fit", help="Fit calibrator")
    fit.add_argument("--score-type", type=str, required=True)
    fit.add_argument("--method", type=str, default="binning")
    fit.add_argument("--json", action="store_true")

    bins = sub.add_parser("bins", help="Show calibration bins")
    bins.add_argument("--score-type", type=str, required=True)
    bins.add_argument("--strategy", type=str)
    bins.add_argument("--json", action="store_true")

    thr = sub.add_parser("thresholds", help="Optimize thresholds")
    thr.add_argument("--score-type", type=str, required=True)
    thr.add_argument("--strategy", type=str)
    thr.add_argument("--objective", type=str, default="net_return_quality")
    thr.add_argument("--json", action="store_true")

    coh = sub.add_parser("cohorts", help="Analyze cohorts")
    coh.add_argument("--score-type", type=str, required=True)
    coh.add_argument("--by", type=str)
    coh.add_argument("--json", action="store_true")

    err = sub.add_parser("errors", help="Error taxonomy")
    err.add_argument("--strategy", type=str)
    err.add_argument("--symbol", type=str)
    err.add_argument("--json", action="store_true")

    rep = sub.add_parser("report", help="Generate calibration report")
    rep.add_argument("--latest", action="store_true")
    rep.add_argument("--json", action="store_true")

    rec = sub.add_parser("recent", help="Show recent calibration events")
    rec.add_argument("--limit", type=int, default=10)
    rec.add_argument("--json", action="store_true")

    cfg = sub.add_parser("config", help="Show calibration config")
    cfg.add_argument("--json", action="store_true")


def _handle_build_outcomes(args, settings):
    builder = create_outcome_dataset_builder(settings)
    records = builder.build_dataset(strategy_name=args.strategy, symbol=args.symbol)
    if args.json:
        print(json.dumps({"count": len(records), "status": "success"}))
    else:
        print(f"Built {len(records)} outcomes.")

def _handle_evaluate(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes(strategy_name=args.strategy)
    calibrator = create_signal_calibrator(settings)
    score_type = CalibrationScoreType(args.score_type.upper())
    result = calibrator.evaluate(records, score_type, OutcomeHorizon.FIVE_DAYS)
    if args.json:
        print(json.dumps(calibration_result_to_dict(result), indent=2))
    else:
        print(format_calibration_result_text(result))

def _handle_fit(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes()
    calibrator = create_signal_calibrator(settings)
    score_type = CalibrationScoreType(args.score_type.upper())
    mapping = calibrator.fit(records, score_type, method=args.method)
    if args.json:
        print(json.dumps(mapping.model_dump(), default=str, indent=2))
    else:
        print(f"Mapping ID: {mapping.mapping_id}, Status: {mapping.status.value}")

def _handle_bins(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes(strategy_name=args.strategy)
    builder = create_calibration_bin_builder(settings)
    score_type = CalibrationScoreType(args.score_type.upper())
    bins = builder.build_bins(records, score_type)
    if args.json:
        print(json.dumps([b.model_dump() for b in bins], default=str, indent=2))
    else:
        for b in bins:
            print(f"{b.lower_bound}-{b.upper_bound}: {b.sample_count} samples")

def _handle_thresholds(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes(strategy_name=args.strategy)
    tuner = create_threshold_tuner(settings)
    score_type = CalibrationScoreType(args.score_type.upper())
    result = tuner.optimize_threshold(records, score_type, OutcomeHorizon.FIVE_DAYS, objective=args.objective)
    if args.json:
        print(json.dumps(threshold_result_to_dict(result), indent=2))
    else:
        print(format_threshold_result_text(result))

def _handle_cohorts(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes()
    analyzer = create_outcome_cohort_analyzer(settings)
    score_type = CalibrationScoreType(args.score_type.upper())
    if args.by:
        cohorts = analyzer.cohort_by_field(records, args.by, score_type)
    else:
        cohorts = analyzer.analyze_cohorts(records, score_type)
    if args.json:
        print(json.dumps([cohort_to_dict(c) for c in cohorts], indent=2))
    else:
        print(format_cohorts_text(cohorts))

def _handle_errors(args, settings):
    store = create_calibration_store(settings)
    records = store.load_outcomes(strategy_name=args.strategy, symbol=args.symbol)
    builder = create_error_taxonomy_builder(settings)
    errors = builder.classify_errors(records, CalibrationScoreType.SIGNAL_CONFIDENCE)
    if args.json:
        print(json.dumps([error_case_to_dict(e) for e in errors], indent=2))
    else:
        print(format_error_cases_text(errors))

def _handle_report(args, settings):
    from bist_signal_bot.calibration.models import CalibrationReport, CalibrationStatus
    from datetime import datetime, UTC
    import uuid

    report = CalibrationReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(UTC),
        overall_status=CalibrationStatus.PASS
    )
    if args.json:
        print(json.dumps(calibration_report_to_dict(report), indent=2))
    else:
        print(format_calibration_report_markdown(report))

def _handle_recent(args, settings):
    store = create_calibration_store(settings)
    res = store.load_latest_calibration()
    out = {"status": "success", "results": [res.model_dump() if res else None]}
    if args.json:
        print(json.dumps(out, default=str, indent=2))
    else:
        print(f"Recent Result: {res.calibration_id if res else 'None'}")

def _handle_config(args, settings):
    keys = [k for k in dir(settings) if k.startswith("CALIBRATION_")]
    conf = {k: getattr(settings, k) for k in keys}
    if args.json:
        print(json.dumps(conf, indent=2))
    else:
        for k, v in conf.items():
            print(f"{k} = {v}")

def handle_calibration_command(args, ctx):
    settings = ctx.settings if hasattr(ctx, 'settings') else Settings()
    cmd = args.calib_cmd

    handlers = {
        "build-outcomes": _handle_build_outcomes,
        "evaluate": _handle_evaluate,
        "fit": _handle_fit,
        "bins": _handle_bins,
        "thresholds": _handle_thresholds,
        "cohorts": _handle_cohorts,
        "errors": _handle_errors,
        "report": _handle_report,
        "recent": _handle_recent,
        "config": _handle_config
    }

    if cmd in handlers:
        handlers[cmd](args, settings)

    return 0
