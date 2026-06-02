import argparse
from pathlib import Path
from typing import Any
import json

from bist_signal_bot.data_import.models import ImportDatasetType
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.app.data_import_app import (
    create_local_data_importer,
    create_import_preview_builder,
    create_schema_mapping_engine,
    create_import_validation_engine,
    create_data_import_store
)
from bist_signal_bot.data_import.reporting import (
    format_preview_text,
    format_mapping_text,
    format_validation_text,
    format_job_text,
    format_data_import_report_markdown,
    job_to_dict,
    report_to_dict
)
from bist_signal_bot.data_import.models import DataImportReport
from datetime import datetime, timezone
import uuid

def add_data_import_parser(subparsers):
    parser = subparsers.add_parser("data-import", help="Manage local data import operations")
    sub = parser.add_subparsers(dest="import_cmd", help="Data import commands")

    # formats
    f_p = sub.add_parser("formats", help="List supported import formats")
    f_p.add_argument("--json", action="store_true", help="Output in JSON")

    # preview
    p_p = sub.add_parser("preview", help="Preview an import source")
    p_p.add_argument("--path", required=True, help="Path to the import source file")
    p_p.add_argument("--type", required=True, choices=[e.value for e in ImportDatasetType], help="Dataset type")
    p_p.add_argument("--json", action="store_true", help="Output in JSON")

    # map
    m_p = sub.add_parser("map", help="Infer schema mapping for an import source")
    m_p.add_argument("--path", required=True, help="Path to the import source file")
    m_p.add_argument("--type", required=True, choices=[e.value for e in ImportDatasetType], help="Dataset type")
    m_p.add_argument("--json", action="store_true", help="Output in JSON")

    # validate
    v_p = sub.add_parser("validate", help="Validate an import source")
    v_p.add_argument("--path", required=True, help="Path to the import source file")
    v_p.add_argument("--type", required=True, choices=[e.value for e in ImportDatasetType], help="Dataset type")
    v_p.add_argument("--json", action="store_true", help="Output in JSON")

    # normalize
    n_p = sub.add_parser("normalize", help="Normalize an import source")
    n_p.add_argument("--path", required=True, help="Path to the import source file")
    n_p.add_argument("--type", required=True, choices=[e.value for e in ImportDatasetType], help="Dataset type")
    n_p.add_argument("--dry-run", action="store_true", help="Run without saving")
    n_p.add_argument("--confirm", action="store_true", help="Confirm writing to disk")
    n_p.add_argument("--json", action="store_true", help="Output in JSON")

    # run
    r_p = sub.add_parser("run", help="Run a full import job")
    r_p.add_argument("--path", required=True, help="Path to the import source file")
    r_p.add_argument("--type", required=True, choices=[e.value for e in ImportDatasetType], help="Dataset type")
    r_p.add_argument("--dry-run", action="store_true", help="Run without saving")
    r_p.add_argument("--confirm", action="store_true", help="Confirm writing to disk")
    r_p.add_argument("--save-catalog", action="store_true", help="Register in Data Catalog")
    r_p.add_argument("--json", action="store_true", help="Output in JSON")

    # jobs
    j_p = sub.add_parser("jobs", help="List recent import jobs")
    j_p.add_argument("--latest", action="store_true", help="Show only the latest job")
    j_p.add_argument("--json", action="store_true", help="Output in JSON")

    # report
    rep_p = sub.add_parser("report", help="Generate or view data import report")
    rep_p.add_argument("--latest", action="store_true", help="Only use the latest job for the report")
    rep_p.add_argument("--json", action="store_true", help="Output in JSON")

    # config
    c_p = sub.add_parser("config", help="Show data import configuration")
    c_p.add_argument("--json", action="store_true", help="Output in JSON")

def handle_data_import_cmd(args, settings: Any = None):
    cmd = args.import_cmd

    if cmd == "formats":
        reg = LocalImportAdapterRegistry(settings)
        formats = [f.value for f in reg.supported_formats()]
        if getattr(args, "json", False):
            print(json.dumps({"supported_formats": formats}, indent=2))
        else:
            print("Supported Formats:")
            for f in formats:
                print(f"  - {f}")

    elif cmd == "preview":
        pb = create_import_preview_builder(settings)
        ds_type = ImportDatasetType(args.type)
        try:
             preview = pb.build_preview(Path(args.path), ds_type)
             preview.source_id = "preview_only"
             if getattr(args, "json", False):
                 print(preview.model_dump_json(indent=2))
             else:
                 print(format_preview_text(preview))
        except Exception as e:
             print(f"Error: {e}")

    elif cmd == "map":
        pb = create_import_preview_builder(settings)
        me = create_schema_mapping_engine(settings)
        ds_type = ImportDatasetType(args.type)
        try:
             preview = pb.build_preview(Path(args.path), ds_type)
             mapping = me.infer_mapping(preview.columns, ds_type)
             if getattr(args, "json", False):
                 print(mapping.model_dump_json(indent=2))
             else:
                 print(format_mapping_text(mapping))
        except Exception as e:
             print(f"Error: {e}")

    elif cmd == "validate":
        importer = create_local_data_importer(settings)
        ds_type = ImportDatasetType(args.type)
        try:
             source = importer.build_source(Path(args.path), ds_type)
             pb = create_import_preview_builder(settings)
             preview = pb.build_preview(Path(args.path), ds_type)
             preview.source_id = source.source_id
             me = create_schema_mapping_engine(settings)
             mapping = me.infer_mapping(preview.columns, ds_type)
             ve = create_import_validation_engine(settings)
             validation = ve.validate_source(source, mapping, preview)
             if getattr(args, "json", False):
                 print(validation.model_dump_json(indent=2))
             else:
                 print(format_validation_text(validation))
        except Exception as e:
             print(f"Error: {e}")

    elif cmd in ("normalize", "run"):
        importer = create_local_data_importer(settings)
        ds_type = ImportDatasetType(args.type)

        # for normalize command, it's just a run command technically
        is_dry = getattr(args, "dry_run", False)
        # default to dry-run if --confirm not specified, else not dry_run
        if getattr(args, "confirm", False):
            is_dry = False
        else:
            is_dry = True

        save_cat = getattr(args, "save_catalog", False)

        try:
            job = importer.run_import(
                path=Path(args.path),
                dataset_type=ds_type,
                dry_run=is_dry,
                confirm=not is_dry,
                save_catalog=save_cat
            )
            if getattr(args, "json", False):
                 print(job.model_dump_json(indent=2))
            else:
                 print(format_job_text(job))
        except Exception as e:
             print(f"Error: {e}")

    elif cmd == "jobs":
        store = create_data_import_store(settings)
        if getattr(args, "latest", False):
            job = store.load_latest_job()
            if not job:
                print("No jobs found." if not getattr(args, "json", False) else "{}")
                return
            if getattr(args, "json", False):
                print(job.model_dump_json(indent=2))
            else:
                print(format_job_text(job))
        else:
            jobs = store.load_jobs(limit=10)
            if not jobs:
                print("No jobs found." if not getattr(args, "json", False) else "[]")
                return
            if getattr(args, "json", False):
                print(json.dumps([job_to_dict(j) for j in jobs], indent=2))
            else:
                for j in jobs:
                    print(f"- {j.job_id} ({j.status}): {j.source.dataset_type} at {j.started_at}")

    elif cmd == "report":
        store = create_data_import_store(settings)
        limit = 1 if getattr(args, "latest", False) else 50
        jobs = store.load_jobs(limit=limit)

        report = DataImportReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc),
            jobs=jobs
        )

        if getattr(args, "json", False):
            print(report.model_dump_json(indent=2))
        else:
            print(format_data_import_report_markdown(report))

    elif cmd == "config":
        # extract import settings
        keys = [k for k in dir(settings) if "DATA_IMPORT" in k] if settings else []
        conf = {}
        if settings:
             for k in keys:
                 val = getattr(settings, k)
                 # secret redact conceptually, but these are bool/ints
                 conf[k] = val
        if getattr(args, "json", False):
             print(json.dumps(conf, indent=2))
        else:
             print("Data Import Config:")
             for k, v in conf.items():
                 print(f"  {k}: {v}")
