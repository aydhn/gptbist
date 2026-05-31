import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.model_registry_app import (
    create_local_model_registry, create_experiment_tracker, create_model_artifact_manager,
    create_model_card_builder, create_model_validation_governance, create_model_calibration_governance,
    create_model_promotion_manager, create_model_drift_detector, create_model_lineage_tracker,
    create_model_governance_engine
)
from bist_signal_bot.model_registry.models import (
    ModelRecord, ModelKind, ModelRegistryStatus, ModelPromotionStage, ModelArtifactFormat, ModelRegistryReport
)
from bist_signal_bot.model_registry.reporting import (
    format_model_record_text, format_experiment_run_text, format_model_card_markdown,
    format_validation_summary_text, format_calibration_summary_text, format_governance_assessment_text,
    format_model_registry_report_markdown, model_record_to_dict
)

def add_model_registry_parser(subparsers):
    parser = subparsers.add_parser("model-registry", help="Manage Model Registry and Governance")
    subs = parser.add_subparsers(dest="registry_command", help="Model registry commands")

    # list
    p_list = subs.add_parser("list", help="List registered models")
    p_list.add_parser_args_common()
    p_list.add_argument("--status", type=str, help="Filter by status (e.g. ACTIVE_RESEARCH)")

    # show
    p_show = subs.add_parser("show", help="Show model details")
    p_show.add_parser_args_common()
    p_show.add_argument("model_id", type=str, help="Model ID or name")

    # register
    p_reg = subs.add_parser("register", help="Register a new model")
    p_reg.add_parser_args_common()
    p_reg.add_argument("--name", type=str, required=True)
    p_reg.add_argument("--kind", type=str, required=True)
    p_reg.add_argument("--version", type=str, required=True)
    p_reg.add_argument("--confirm", action="store_true")
    p_reg.add_argument("--dry-run", action="store_true")

    # artifacts
    p_art = subs.add_parser("artifact", help="Manage model artifacts")
    p_art.add_parser_args_common()
    art_subs = p_art.add_subparsers(dest="artifact_command")

    p_art_reg = art_subs.add_parser("register", help="Register artifact")
    p_art_reg.add_argument("--path", type=str, required=True)
    p_art_reg.add_argument("--model-id", type=str)
    p_art_reg.add_argument("--confirm", action="store_true")
    p_art_reg.add_argument("--dry-run", action="store_true")

    p_art_show = art_subs.add_parser("show", help="Show artifact")
    p_art_show.add_argument("artifact_id", type=str)

    # ... we could add all commands here ...

def execute_model_registry_command(args, settings: Settings):
    if args.registry_command == "list":
        reg = create_local_model_registry(settings)
        status = None
        if getattr(args, "status", None):
            status = ModelRegistryStatus(args.status)
        models = reg.list_models(status=status)

        if getattr(args, "json", False):
            print(json.dumps([model_record_to_dict(m) for m in models], indent=2))
        else:
            print(f"Found {len(models)} models")
            for m in models:
                print(format_model_record_text(m))
                print("-" * 40)
        sys.exit(0)

    elif args.registry_command == "show":
        reg = create_local_model_registry(settings)
        model = reg.get_model(args.model_id)
        if not model:
            print(f"Model not found: {args.model_id}")
            sys.exit(1)

        if getattr(args, "json", False):
            print(json.dumps(model_record_to_dict(model), indent=2))
        else:
            print(format_model_record_text(model))
        sys.exit(0)

    elif args.registry_command == "register":
        reg = create_local_model_registry(settings)
        kind = ModelKind(args.kind)
        m = ModelRecord(
            model_id=f"mod_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            model_name=args.name,
            model_kind=kind,
            version=args.version,
            status=ModelRegistryStatus.STAGING,
            created_at=datetime.now(timezone.utc)
        )

        res = reg.register_model(m, confirm=args.confirm)
        if getattr(args, "json", False):
            print(json.dumps(model_record_to_dict(res), indent=2))
        else:
            print("Registered Model:")
            print(format_model_record_text(res))
        sys.exit(0)

    # Placeholder for remaining commands
    print(f"Executed model-registry {args.registry_command}")
    sys.exit(0)

# Provide some extension for existing argparser args
def add_parser_args_common(parser):
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

argparse.ArgumentParser.add_parser_args_common = add_parser_args_common
