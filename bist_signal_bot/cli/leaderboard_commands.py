import argparse
import uuid
from datetime import datetime
from bist_signal_bot.cli_ux.models import CLIOutputMode, CLIStatus, CLIOutputEnvelope
from bist_signal_bot.app.leaderboard_app import (
    create_leaderboard_store, create_benchmark_cohort_builder, create_leaderboard_data_collector,
    create_candidate_ranking_engine, create_candidate_comparison_engine, create_selection_policy_registry,
    create_candidate_selection_engine
)
from bist_signal_bot.leaderboard.models import CandidateType, BenchmarkCohortType
from bist_signal_bot.leaderboard.reporting import (
    cohort_to_dict, format_cohort_text, leaderboard_to_dict, format_leaderboard_text,
    comparison_to_dict, format_comparison_text, policy_to_dict, selection_result_to_dict,
    format_selection_result_text, leaderboard_report_to_dict, format_leaderboard_report_markdown
)
from bist_signal_bot.leaderboard.models import LeaderboardReport

def create_envelope(data, message):
    return CLIOutputEnvelope(
        envelope_id=f"env_{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(),
        command="leaderboard",
        status=CLIStatus.SUCCESS,
        exit_code=0,
        output_mode=CLIOutputMode.JSON if data else CLIOutputMode.TEXT,
        payload=data,
        metadata={"message": message}
    )

def create_error_envelope(message):
    return CLIOutputEnvelope(
        envelope_id=f"env_{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(),
        command="leaderboard",
        status=CLIStatus.FAILED,
        exit_code=1,
        output_mode=CLIOutputMode.TEXT,
        payload={},
        errors=[message]
    )

def handle_leaderboard_cohorts(args):
    builder = create_benchmark_cohort_builder()
    cohorts = builder.default_cohorts()

    if args.json:
        return create_envelope(data=[cohort_to_dict(c) for c in cohorts], message="Cohorts loaded.")

    lines = [format_cohort_text(c) for c in cohorts]
    return create_envelope(data={}, message="\n\n".join(lines))

def handle_leaderboard_build(args):
    builder = create_benchmark_cohort_builder()
    collector = create_leaderboard_data_collector()
    ranking_engine = create_candidate_ranking_engine()
    store = create_leaderboard_store()

    c_type = args.type
    if c_type == "STRATEGY_COHORT":
        cohort = builder.build_strategy_cohort(args.candidates)
    elif c_type == "MODEL_COHORT":
        cohort = builder.build_model_cohort(args.candidates)
    else:
        cohort = builder.build_feature_set_cohort(args.candidates)

    candidates = []
    for cid in cohort.candidate_ids:
        c = collector.collect_candidate(cohort.candidate_type, cid)
        candidates.append(c)

    lb = ranking_engine.build_leaderboard(cohort, candidates)

    if args.save:
        store.append_cohort(cohort)
        for c in candidates:
            store.append_candidate(c)
        store.append_leaderboard(lb)

    if args.json:
        return create_envelope(data=leaderboard_to_dict(lb), message="Leaderboard built.")

    return create_envelope(data={}, message=format_leaderboard_text(lb))

def handle_leaderboard_show(args):
    store = create_leaderboard_store()

    if args.latest:
        lb = store.load_latest_leaderboard()
    else:
        lbs = store.load_leaderboards()
        lb = next((l for l in lbs if l.leaderboard_id == args.id), None)

    if not lb:
        return create_error_envelope(message="Leaderboard not found.")

    if args.json:
        return create_envelope(data=leaderboard_to_dict(lb), message="Leaderboard loaded.")

    return create_envelope(data={}, message=format_leaderboard_text(lb))

def handle_leaderboard_rank(args):
    collector = create_leaderboard_data_collector()
    ranking_engine = create_candidate_ranking_engine()
    builder = create_benchmark_cohort_builder()

    c_type = CandidateType(args.candidate_type)
    c = collector.collect_candidate(c_type, args.candidate_id)

    if c_type == CandidateType.STRATEGY:
        cohort = builder.build_strategy_cohort([args.candidate_id])
    else:
        cohort = builder.build_model_cohort([args.candidate_id])

    lb = ranking_engine.build_leaderboard(cohort, [c])

    if args.json:
        return create_envelope(data=leaderboard_to_dict(lb), message="Ranked candidate.")

    return create_envelope(data={}, message=format_leaderboard_text(lb))

def handle_leaderboard_compare(args):
    collector = create_leaderboard_data_collector()
    compare_engine = create_candidate_comparison_engine()
    store = create_leaderboard_store()

    c_type = CandidateType(args.type)
    ca = collector.collect_candidate(c_type, args.a)
    cb = collector.collect_candidate(c_type, args.b)

    comp = compare_engine.compare(ca, cb)
    store.append_comparison(comp)

    if args.json:
        return create_envelope(data=comparison_to_dict(comp), message="Comparison generated.")

    return create_envelope(data={}, message=format_comparison_text(comp))

def handle_leaderboard_policies(args):
    registry = create_selection_policy_registry()
    policies = registry.default_policies()

    if hasattr(args, "show") and args.show:
        p = registry.get_policy(args.show)
        if not p:
            return create_error_envelope(message="Policy not found.")
        if args.json:
            return create_envelope(data=policy_to_dict(p), message="Policy loaded.")
        return create_envelope(data={}, message=f"Policy: {p.name}\nWeights: {p.weights}")

    if args.json:
        return create_envelope(data=[policy_to_dict(p) for p in policies], message="Policies loaded.")

    lines = [f"{p.policy_id}: {p.name}" for p in policies]
    return create_envelope(data={}, message="\n".join(lines))

def handle_leaderboard_select(args):
    store = create_leaderboard_store()
    selection_engine = create_candidate_selection_engine()
    registry = create_selection_policy_registry()

    if args.latest:
        lb = store.load_latest_leaderboard()
    else:
        lbs = store.load_leaderboards()
        lb = next((l for l in lbs if l.leaderboard_id == args.leaderboard_id), None)

    if not lb:
        return create_error_envelope(message="Leaderboard not found.")

    policy = registry.get_policy(args.policy) if hasattr(args, "policy") and args.policy else None

    res = selection_engine.select_from_leaderboard(lb, policy)
    store.append_selection(res)

    if args.json:
        return create_envelope(data=selection_result_to_dict(res), message="Selection complete.")

    return create_envelope(data={}, message=format_selection_result_text(res))

def handle_leaderboard_report(args):
    store = create_leaderboard_store()

    report = LeaderboardReport(report_id=f"rep_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    lb = store.load_latest_leaderboard()
    if lb:
        report.leaderboards = [lb]

    md = format_leaderboard_report_markdown(report)
    paths = store.save_report(report, md)

    if args.json:
        return create_envelope(data=leaderboard_report_to_dict(report), message=f"Report saved to {paths['json']}")

    return create_envelope(data={}, message=md + f"\n\nReport saved to {paths['markdown']}")

def handle_leaderboard_recent(args):
    store = create_leaderboard_store()
    lbs = store.load_leaderboards(limit=args.limit)

    if args.json:
        return create_envelope(data=[leaderboard_to_dict(l) for l in lbs], message="Recent loaded.")

    lines = [f"{l.leaderboard_id} | Cohort: {l.cohort_id} | Status: {l.status.value}" for l in lbs]
    if not lines:
        lines = ["No recent leaderboards found."]

    return create_envelope(data={}, message="\n".join(lines))

def handle_leaderboard_config(args):
    from bist_signal_bot.config.settings import get_settings
    settings = get_settings()

    d = {k: v for k, v in settings.model_dump().items() if "LEADERBOARD" in k}

    if args.json:
        return create_envelope(data=d, message="Leaderboard config.")

    lines = [f"{k}: {v}" for k, v in d.items()]
    return create_envelope(data={}, message="\n".join(lines))

def add_leaderboard_parser(subparsers):
    parser = subparsers.add_parser("leaderboard", help="Research Leaderboard Management")
    sub = parser.add_subparsers(dest="lb_command", required=True)

    c = sub.add_parser("cohorts", help="Show benchmark cohorts")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=handle_leaderboard_cohorts)

    b = sub.add_parser("build", help="Build a leaderboard")
    b.add_argument("--type", type=str, default="STRATEGY_COHORT")
    b.add_argument("--candidates", nargs="+", default=[])
    b.add_argument("--save", action="store_true")
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=handle_leaderboard_build)

    s = sub.add_parser("show", help="Show a leaderboard")
    s.add_argument("id", nargs="?", default="")
    s.add_argument("--latest", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=handle_leaderboard_show)

    r = sub.add_parser("rank", help="Rank a candidate")
    r.add_argument("--candidate-type", type=str, required=True)
    r.add_argument("--candidate-id", type=str, required=True)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=handle_leaderboard_rank)

    comp = sub.add_parser("compare", help="Compare candidates")
    comp.add_argument("--type", type=str, required=True)
    comp.add_argument("--a", type=str, required=True)
    comp.add_argument("--b", type=str, required=True)
    comp.add_argument("--json", action="store_true")
    comp.set_defaults(func=handle_leaderboard_compare)

    p = sub.add_parser("policies", help="Show selection policies")
    p.add_argument("show", nargs="?", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=handle_leaderboard_policies)

    sel = sub.add_parser("select", help="Select candidates")
    sel.add_argument("--leaderboard-id", type=str, default="")
    sel.add_argument("--latest", action="store_true")
    sel.add_argument("--policy", type=str, default="")
    sel.add_argument("--json", action="store_true")
    sel.set_defaults(func=handle_leaderboard_select)

    rep = sub.add_parser("report", help="Generate report")
    rep.add_argument("--latest", action="store_true")
    rep.add_argument("--json", action="store_true")
    rep.set_defaults(func=handle_leaderboard_report)

    rec = sub.add_parser("recent", help="Show recent leaderboards")
    rec.add_argument("--limit", type=int, default=10)
    rec.add_argument("--json", action="store_true")
    rec.set_defaults(func=handle_leaderboard_recent)

    conf = sub.add_parser("config", help="Show leaderboard config")
    conf.add_argument("--json", action="store_true")
    conf.set_defaults(func=handle_leaderboard_config)
