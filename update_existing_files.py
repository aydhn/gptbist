import os
import re

def insert_exceptions():
    path = "bist_signal_bot/core/exceptions.py"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()

    new_ex = """
class BootstrapError(BistSignalBotError):
    pass

class RunProfileError(BootstrapError):
    pass

class BootstrapInitializationError(BootstrapError):
    pass

class BootstrapValidationError(BootstrapError):
    pass

class OfflineDemoError(BootstrapError):
    pass

class CommandRecipeError(BootstrapError):
    pass

class ReleaseBundleError(BootstrapError):
    pass

class OnboardingError(BootstrapError):
    pass

class BootstrapStorageError(BootstrapError):
    pass
"""
    if "class BootstrapError" not in content:
        with open(path, "a") as f: f.write(new_ex)


def insert_paths():
    path = "bist_signal_bot/storage/paths.py"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()

    new_path = """
def get_bootstrap_dir(settings: 'Settings | None' = None) -> Path:
    base = get_base_dir(settings)
    if settings and hasattr(settings, 'BOOTSTRAP_DIR_NAME') and settings.BOOTSTRAP_DIR_NAME:
        return base / settings.BOOTSTRAP_DIR_NAME
    return base / "bootstrap"
"""
    if "def get_bootstrap_dir" not in content:
        with open(path, "a") as f: f.write(new_path)


def update_audit():
    path = "bist_signal_bot/core/audit.py"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()

    new_audit = """    BOOTSTRAP_PROFILE_SELECTED = "BOOTSTRAP_PROFILE_SELECTED"
    BOOTSTRAP_INIT_STARTED = "BOOTSTRAP_INIT_STARTED"
    BOOTSTRAP_INIT_COMPLETED = "BOOTSTRAP_INIT_COMPLETED"
    BOOTSTRAP_VALIDATION_RUN = "BOOTSTRAP_VALIDATION_RUN"
    OFFLINE_DEMO_RUN = "OFFLINE_DEMO_RUN"
    COMMAND_RECIPES_RENDERED = "COMMAND_RECIPES_RENDERED"
    ONBOARDING_GUIDE_CREATED = "ONBOARDING_GUIDE_CREATED"
    RELEASE_BUNDLE_CREATED = "RELEASE_BUNDLE_CREATED"
    BOOTSTRAP_REPORT_CREATED = "BOOTSTRAP_REPORT_CREATED"
"""
    if "BOOTSTRAP_PROFILE_SELECTED" not in content:
        content = content.replace("class AuditEventType(str, Enum):", "class AuditEventType(str, Enum):\n" + new_audit)
        with open(path, "w") as f: f.write(content)

def update_settings():
    path = "bist_signal_bot/config/settings.py"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()

    new_settings = """
    # Bootstrap
    ENABLE_BOOTSTRAP: bool = True
    BOOTSTRAP_DIR_NAME: str = "bootstrap"
    BOOTSTRAP_RESEARCH_ONLY: bool = True
    BOOTSTRAP_SAVE_RESULTS: bool = True

    BOOTSTRAP_DEFAULT_PROFILE: str = "STANDARD"
    BOOTSTRAP_ALLOW_CUSTOM_PROFILE: bool = True
    BOOTSTRAP_BLOCK_UNSAFE_PROFILE: bool = True
    BOOTSTRAP_REQUIRE_NO_REAL_ORDER: bool = True
    BOOTSTRAP_REQUIRE_NO_EXTERNAL_CALLS_FOR_DEMO: bool = True

    BOOTSTRAP_INIT_REQUIRES_CONFIRM: bool = True
    BOOTSTRAP_CREATE_DEFAULT_DIRS: bool = True
    BOOTSTRAP_WRITE_ENV_TEMPLATE: bool = True
    BOOTSTRAP_COPY_DEMO_FIXTURES: bool = True
    BOOTSTRAP_OVERWRITE_REQUIRES_CONFIRM: bool = True

    BOOTSTRAP_MIN_PYTHON_VERSION: str = "3.10"
    BOOTSTRAP_VALIDATE_IMPORTS: bool = True
    BOOTSTRAP_VALIDATE_PATHS: bool = True
    BOOTSTRAP_VALIDATE_FIXTURES: bool = True
    BOOTSTRAP_VALIDATE_SECURITY: bool = True
    BOOTSTRAP_VALIDATE_CLI: bool = True

    BOOTSTRAP_DEMO_PROFILE: str = "DEMO"
    BOOTSTRAP_DEMO_SAVE_RUN: bool = True
    BOOTSTRAP_DEMO_USE_SYNTHETIC_FIXTURES: bool = True
    BOOTSTRAP_DEMO_BLOCK_EXTERNAL_CALLS: bool = True
    BOOTSTRAP_DEMO_TIMEOUT_SECONDS: int = 60

    BOOTSTRAP_SAVE_COMMAND_RECIPES: bool = True
    BOOTSTRAP_INCLUDE_EXAMPLES: bool = True

    BOOTSTRAP_BUILD_RELEASE_BUNDLE: bool = True
    BOOTSTRAP_RELEASE_SCHEMA_VERSION: str = "1.0"
    BOOTSTRAP_RELEASE_INCLUDE_QA_STATUS: bool = True
    BOOTSTRAP_RELEASE_INCLUDE_OPS_STATUS: bool = True
    BOOTSTRAP_RELEASE_INCLUDE_REPRO_PACK: bool = True

    RUNTIME_ACTIVE_RUN_PROFILE: str = "STANDARD"
    RUNTIME_BOOTSTRAP_VALIDATE_ON_START: bool = False

    REPORT_INCLUDE_BOOTSTRAP: bool = True
    RESEARCH_AUTO_LOG_BOOTSTRAP: bool = False
"""
    if "ENABLE_BOOTSTRAP:" not in content:
        content = content.replace("class Settings(BaseSettings):", "class Settings(BaseSettings):" + new_settings)
        with open(path, "w") as f: f.write(content)

def update_commands():
    path = "bist_signal_bot/cli/commands.py"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()

    bs_import = "from bist_signal_bot.cli.bootstrap_cli import handle_bootstrap\n"
    if bs_import not in content:
        content = content.replace("import sys", "import sys\n" + bs_import)

    bs_cmds = """
    # Bootstrap
    bs_parser = subparsers.add_parser("bootstrap", help="Local MVP packaging and demo")
    bs_sub = bs_parser.add_subparsers(dest="bootstrap_cmd")

    bs_prof = bs_sub.add_parser("profiles")
    bs_prof.add_argument("action", nargs="?", choices=["show"])
    bs_prof.add_argument("name", nargs="?")
    bs_prof.add_argument("--json", action="store_true")

    bs_init = bs_sub.add_parser("init")
    bs_init.add_argument("--profile", default="STANDARD")
    bs_init.add_argument("--base-dir", default=None)
    bs_init.add_argument("--confirm", action="store_true")
    bs_init.add_argument("--dry-run", action="store_true")
    bs_init.add_argument("--json", action="store_true")

    bs_val = bs_sub.add_parser("validate")
    bs_val.add_argument("--profile", default="STANDARD")
    bs_val.add_argument("--json", action="store_true")

    bs_demo = bs_sub.add_parser("demo")
    bs_demo.add_argument("--save", action="store_true")
    bs_demo.add_argument("--json", action="store_true")

    bs_rec = bs_sub.add_parser("recipes")
    bs_rec.add_argument("action", nargs="?", choices=["list", "show"], default="list")
    bs_rec.add_argument("name", nargs="?")
    bs_rec.add_argument("--profile", default="STANDARD")
    bs_rec.add_argument("--json", action="store_true")

    bs_onb = bs_sub.add_parser("onboarding")
    bs_onb.add_argument("--profile", default="STANDARD")
    bs_onb.add_argument("--json", action="store_true")

    bs_rel = bs_sub.add_parser("release-bundle")
    bs_rel.add_argument("--profile", default="STANDARD")
    bs_rel.add_argument("--include-qa", action="store_true")
    bs_rel.add_argument("--include-ops", action="store_true")
    bs_rel.add_argument("--json", action="store_true")

    bs_rep = bs_sub.add_parser("report")
    bs_rep.add_argument("--latest", action="store_true")
    bs_rep.add_argument("--json", action="store_true")

    bs_recent = bs_sub.add_parser("recent")
    bs_recent.add_argument("--limit", type=int, default=10)
    bs_recent.add_argument("--json", action="store_true")

    bs_conf = bs_sub.add_parser("config")
    bs_conf.add_argument("--json", action="store_true")
"""
    if "bs_parser = subparsers.add_parser(\"bootstrap\"" not in content:
        content = content.replace("    return parser.parse_args(args)", bs_cmds + "\n    return parser.parse_args(args)")

    if "elif args.command == \"bootstrap\":" not in content:
        content = content.replace("    else:\n        parser.print_help()", "    elif args.command == \"bootstrap\":\n        handle_bootstrap(args)\n    else:\n        parser.print_help()")

    # Add --bootstrap to existing commands
    content = content.replace('hc_parser = subparsers.add_parser("healthcheck"', 'hc_parser = subparsers.add_parser("healthcheck"\n    hc_parser.add_argument("--bootstrap", action="store_true")')
    content = content.replace('doc_parser = subparsers.add_parser("doctor"', 'doc_parser = subparsers.add_parser("doctor"\n    doc_parser.add_argument("--bootstrap", action="store_true")')
    content = content.replace('rg_parser = qa_sub.add_parser("release-gate"', 'rg_parser = qa_sub.add_parser("release-gate"\n    rg_parser.add_argument("--include-bootstrap", action="store_true")')
    content = content.replace('rd_parser = ops_sub.add_parser("readiness"', 'rd_parser = ops_sub.add_parser("readiness"\n    rd_parser.add_argument("--include-bootstrap", action="store_true")')
    content = content.replace('daily_parser = rep_sub.add_parser("daily"', 'daily_parser = rep_sub.add_parser("daily"\n    daily_parser.add_argument("--include-bootstrap", action="store_true")')

    with open(path, "w") as f: f.write(content)


insert_exceptions()
insert_paths()
update_audit()
update_settings()
update_commands()
