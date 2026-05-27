import argparse
from pathlib import Path
import json

from bist_signal_bot.app.disclosures_app import (
    create_disclosure_importer,
    create_disclosure_store,
    create_disclosure_normalizer,
    create_disclosure_classifier,
    create_disclosure_event_extractor,
    create_disclosure_impact_assessor,
    create_disclosure_digest_builder,
    create_disclosure_entity_linker
)

def handle_disclosures(args):
    cmd = args.subcommand
    store = create_disclosure_store()

    if cmd == "import":
        importer = create_disclosure_importer()
        is_confirm = args.confirm

        if args.file:
            result = importer.import_file(Path(args.file), confirm=is_confirm)
        elif args.folder:
            result = importer.import_folder(Path(args.folder), confirm=is_confirm)
        else:
            print("You must provide --file or --folder")
            return

        print(f"Imported {result.disclosures_imported} records. Found {result.rows_seen} total.")
        if not is_confirm:
            print("DRY RUN: Records not saved. Use --confirm to save.")

    elif cmd == "list":
        records = store.load_records(symbol=args.symbol, limit=args.limit or 50)
        if args.json:
            print(json.dumps([r.model_dump() for r in records], default=str, indent=2))
        else:
            for r in records:
                print(f"{r.disclosure_id} - [{','.join(r.symbols)}] - {r.title} ({r.severity.value})")

    elif cmd == "show":
        record = store.get_record(args.disclosure_id)
        if not record:
            print("Not found.")
            return
        if args.json:
            print(json.dumps(record.model_dump(), default=str, indent=2))
        else:
            print(f"ID: {record.disclosure_id}\\nTitle: {record.title}\\nBody: {record.body}\\nSeverity: {record.severity.value}")

    elif cmd == "classify":
        record = store.get_record(args.disclosure_id)
        if not record:
            print("Not found.")
            return
        classifier = create_disclosure_classifier()
        record = classifier.classify(record)
        if args.json:
            print(json.dumps(record.model_dump(), default=str, indent=2))
        else:
            print(f"Type: {record.disclosure_type.value}\\nSentiment: {record.sentiment.value}\\nSeverity: {record.severity.value}")

    elif cmd == "extract":
        record = store.get_record(args.disclosure_id)
        if not record:
            print("Not found.")
            return
        extractor = create_disclosure_event_extractor()
        extractions = extractor.extract_events(record)
        if args.json:
            print(json.dumps([e.model_dump() for e in extractions], default=str, indent=2))
        else:
            for e in extractions:
                print(f"Event: {e.extracted_event_type} on {e.event_date}")

    elif cmd == "assess":
        record = store.get_record(args.disclosure_id)
        if not record:
            print("Not found.")
            return
        assessor = create_disclosure_impact_assessor()
        assessment = assessor.assess(record)
        if args.json:
            print(json.dumps(assessment.model_dump(), default=str, indent=2))
        else:
            print(f"Narrative Risk: {assessment.narrative_risk_score}\\nDecision: {assessment.recommended_decision}")

    elif cmd == "digest":
        records = store.load_records(symbol=args.symbol, limit=50)
        builder = create_disclosure_digest_builder()
        digest = builder.build_digest(records)
        if args.json:
            print(json.dumps(digest.model_dump(), default=str, indent=2))
        else:
            print(f"Title: {digest.title}\\nSummary: {digest.summary}\\nHigh Severity: {digest.high_severity_count}")

    elif cmd == "link-events":
        record = store.get_record(args.disclosure_id)
        if not record:
            print("Not found.")
            return
        linker = create_disclosure_entity_linker()
        links = linker.link_entities(record)
        if args.json:
            print(json.dumps([l.model_dump() for l in links], default=str, indent=2))
        else:
            for l in links:
                print(f"Link: {l.entity_type} -> {l.entity_value} (Conf: {l.confidence})")

    elif cmd == "report":
        print("Report building is mocked. Use output from 'assess' or 'digest' for insights.")

    elif cmd == "recent":
        records = store.load_records(limit=args.limit or 10)
        if args.json:
            print(json.dumps([r.model_dump() for r in records], default=str, indent=2))
        else:
            for r in records:
                print(f"{r.disclosure_id} - {r.title}")

    elif cmd == "config":
        from bist_signal_bot.config.settings import get_settings
        s = get_settings()
        cfg = {k: v for k, v in s.model_dump().items() if 'DISCLOSURE' in k.upper()}
        if args.json:
            print(json.dumps(cfg, indent=2))
        else:
            for k, v in cfg.items():
                print(f"{k}: {v}")
    else:
        print(f"Unknown disclosure command: {cmd}")

def add_disclosures_parser(subparsers):
    p = subparsers.add_parser("disclosures", help="Manage Disclosure Intelligence")
    sp = p.add_subparsers(dest="subcommand", required=True)

    # import
    p_imp = sp.add_parser("import", help="Import disclosures")
    p_imp.add_argument("--file", help="CSV or JSON file path")
    p_imp.add_argument("--folder", help="TXT folder path")
    p_imp.add_argument("--dry-run", action="store_true", help="Do not save")
    p_imp.add_argument("--confirm", action="store_true", help="Save to store")

    # list
    p_list = sp.add_parser("list", help="List disclosures")
    p_list.add_argument("--symbol")
    p_list.add_argument("--type", dest="disclosure_type")
    p_list.add_argument("--limit", type=int, default=50)
    p_list.add_argument("--json", action="store_true")

    # show
    p_show = sp.add_parser("show", help="Show disclosure")
    p_show.add_argument("disclosure_id")
    p_show.add_argument("--json", action="store_true")

    # classify
    p_class = sp.add_parser("classify", help="Classify disclosure")
    p_class.add_argument("disclosure_id")
    p_class.add_argument("--json", action="store_true")

    # extract
    p_ext = sp.add_parser("extract", help="Extract events from disclosure")
    p_ext.add_argument("disclosure_id")
    p_ext.add_argument("--create-event", action="store_true")
    p_ext.add_argument("--confirm", action="store_true")
    p_ext.add_argument("--json", action="store_true")

    # assess
    p_assess = sp.add_parser("assess", help="Assess disclosure impact")
    p_assess.add_argument("disclosure_id")
    p_assess.add_argument("--json", action="store_true")

    # digest
    p_dig = sp.add_parser("digest", help="Build digest")
    p_dig.add_argument("--symbol")
    p_dig.add_argument("--json", action="store_true")

    # link-events
    p_link = sp.add_parser("link-events", help="Link entities in disclosure")
    p_link.add_argument("disclosure_id")
    p_link.add_argument("--json", action="store_true")

    # report
    p_rep = sp.add_parser("report", help="Generate disclosure report")
    p_rep.add_argument("--latest", action="store_true")
    p_rep.add_argument("--json", action="store_true")

    # recent
    p_rec = sp.add_parser("recent", help="Show recent disclosures")
    p_rec.add_argument("--limit", type=int, default=10)
    p_rec.add_argument("--json", action="store_true")

    # config
    p_conf = sp.add_parser("config", help="Show disclosure config")
    p_conf.add_argument("--json", action="store_true")
