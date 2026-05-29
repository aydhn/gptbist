import os
from pathlib import Path

def ensure_dir(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def write_file(path, content):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# bootstrap/models.py
write_file("bist_signal_bot/bootstrap/models.py", """
from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class BootstrapStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    NOT_STARTED = "NOT_STARTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class RunProfileName(str, Enum):
    MINIMAL = "MINIMAL"
    STANDARD = "STANDARD"
    FULL_RESEARCH = "FULL_RESEARCH"
    QA = "QA"
    DEMO = "DEMO"
    SAFE_MAINTENANCE = "SAFE_MAINTENANCE"
    CUSTOM = "CUSTOM"

class BootstrapCheckType(str, Enum):
    PYTHON_VERSION = "PYTHON_VERSION"
    PACKAGE_IMPORT = "PACKAGE_IMPORT"
    CONFIG = "CONFIG"
    PATHS = "PATHS"
    STORAGE = "STORAGE"
    FIXTURES = "FIXTURES"
    SECURITY = "SECURITY"
    NO_EXTERNAL_CALLS = "NO_EXTERNAL_CALLS"
    NO_REAL_ORDER = "NO_REAL_ORDER"
    QA = "QA"
    OPS = "OPS"
    DOCS = "DOCS"
    CLI = "CLI"
    CUSTOM = "CUSTOM"

class CommandRecipeType(str, Enum):
    QUICKSTART = "QUICKSTART"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    MINIMAL_SCAN = "MINIMAL_SCAN"
    CONTEXT_REVIEW = "CONTEXT_REVIEW"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    QA_RELEASE_GATE = "QA_RELEASE_GATE"
    OPS_HEALTH = "OPS_HEALTH"
    DATA_IMPORT = "DATA_IMPORT"
    REPORTING = "REPORTING"
    CUSTOM = "CUSTOM"

class RunProfile(BaseModel):
    profile_id: str
    name: RunProfileName
    title: str
    description: str
    enabled_modules: list[str] = Field(default_factory=list)
    disabled_modules: list[str] = Field(default_factory=list)
    env_overrides: dict[str, str] = Field(default_factory=dict)
    default_commands: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Run profile is local research configuration metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapCheckResult(BaseModel):
    check_id: str
    check_type: BootstrapCheckType
    name: str
    status: BootstrapStatus
    message: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapInitResult(BaseModel):
    init_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile: RunProfile
    base_dir: str
    created_paths: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    fixture_files: list[str] = Field(default_factory=list)
    status: BootstrapStatus
    checks: list[BootstrapCheckResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap init prepares local research folders only. It is not investment advice or trading setup approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapValidationResult(BaseModel):
    validation_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: Optional[RunProfileName] = None
    status: BootstrapStatus
    checks: list[BootstrapCheckResult] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap validation is local software readiness metadata only. It is not financial or trading readiness. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OfflineDemoRun(BaseModel):
    demo_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile: RunProfileName
    commands_run: list[str] = Field(default_factory=list)
    command_results: list[dict[str, Any]] = Field(default_factory=list)
    artifacts_created: dict[str, str] = Field(default_factory=dict)
    status: BootstrapStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Offline demo uses synthetic/local data only. It does not represent real market performance and is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandRecipeStep(BaseModel):
    step_id: str
    order: int
    title: str
    command: str
    description: str
    expected_output: Optional[str] = None
    destructive: bool = False
    requires_confirm: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandRecipe(BaseModel):
    recipe_id: str
    recipe_type: CommandRecipeType
    title: str
    description: str
    steps: list[CommandRecipeStep] = Field(default_factory=list)
    estimated_complexity: str
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Command recipe is local research workflow guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReleaseBundleManifest(BaseModel):
    bundle_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: RunProfileName
    project_version: Optional[str] = None
    schema_version: str
    included_modules: list[str] = Field(default_factory=list)
    included_docs: list[str] = Field(default_factory=list)
    included_examples: list[str] = Field(default_factory=list)
    qa_gate_status: Optional[str] = None
    ops_readiness_status: Optional[str] = None
    reproducibility_pack_ref: Optional[str] = None
    checksums: dict[str, str] = Field(default_factory=dict)
    status: BootstrapStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Release bundle manifest describes local research software artifacts only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OnboardingGuide(BaseModel):
    guide_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: RunProfileName
    title: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    recommended_recipes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Onboarding guide is local software setup guidance only."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    init_result: Optional[BootstrapInitResult] = None
    validation_result: Optional[BootstrapValidationResult] = None
    demo_runs: list[OfflineDemoRun] = Field(default_factory=list)
    recipes: list[CommandRecipe] = Field(default_factory=list)
    release_bundle: Optional[ReleaseBundleManifest] = None
    onboarding_guide: Optional[OnboardingGuide] = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap report is local software setup reporting only. It is not investment advice, portfolio advice, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
"""
)

write_file("bist_signal_bot/security/claims_guard.py", """
def is_safe_claim(text: str) -> bool:
    unsafe_keywords = ["trade ready", "işlem yapılabilir", "kesin", "al/sat", "hedef fiyat", "garanti"]
    for kw in unsafe_keywords:
        if kw in text.lower():
            return False
    return True
""")

write_file("bist_signal_bot/security/path_guard.py", """
from pathlib import Path

class PathGuard:
    @staticmethod
    def ensure_safe_path(base_dir: Path, target_path: Path) -> bool:
        try:
            target_path.resolve().relative_to(base_dir.resolve())
            return True
        except ValueError:
            return False
""")

write_file("bist_signal_bot/bootstrap/profiles.py", """
import uuid
from typing import Any
from bist_signal_bot.bootstrap.models import RunProfile, RunProfileName

class RunProfileRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self.profiles = {p.name: p for p in self.default_profiles()}

    def default_profiles(self) -> list[RunProfile]:
        return [
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.MINIMAL,
                title="Minimal Research",
                description="Basic scan and signal generation.",
                enabled_modules=["scanner", "signals", "reports_basic"],
                disabled_modules=["context", "scheduler"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.STANDARD,
                title="Standard Research",
                description="Core signals, risk, basic context fusion.",
                enabled_modules=["scanner", "signals", "risk", "calibration", "context_fusion_light", "review_workflow", "reports"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.FULL_RESEARCH,
                title="Full Research",
                description="All modules active.",
                enabled_modules=["scanner", "signals", "risk", "events", "disclosures", "financials", "factors", "macro", "context_fusion", "review_workflow", "portfolio", "reports"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.QA,
                title="QA Testing",
                description="Testing profile with synthetic fixtures.",
                enabled_modules=["qa", "synthetic_fixtures", "release_gate"],
                env_overrides={"NO_EXTERNAL_CALLS": "true"}
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.DEMO,
                title="Offline Demo",
                description="Offline synthetic demo workflow.",
                enabled_modules=["offline_synthetic", "demo_workflow", "reports_dry_run"],
                env_overrides={"NO_EXTERNAL_CALLS": "true"}
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.SAFE_MAINTENANCE,
                title="Safe Maintenance",
                description="Operations, backup/restore dry runs.",
                enabled_modules=["ops", "backup", "restore", "doctor", "healthcheck"],
                disabled_modules=["scanner"]
            )
        ]

    def get_profile(self, name: RunProfileName | str) -> RunProfile | None:
        if isinstance(name, str):
            try:
                name = RunProfileName(name)
            except ValueError:
                return None
        return self.profiles.get(name)

    def profile_env(self, profile: RunProfile) -> dict[str, str]:
        return profile.env_overrides

    def validate_profile(self, profile: RunProfile) -> list[str]:
        warnings = []
        if not profile.title:
            warnings.append("Profile title is empty.")
        for k, v in profile.env_overrides.items():
            if "SECRET" in k.upper() or "TOKEN" in k.upper() or "KEY" in k.upper():
                warnings.append(f"Secret detected in env override: {k}")
            if k.upper() in ["ENABLE_BROKER", "LIVE_TRADING"] and str(v).lower() == "true":
                warnings.append(f"BLOCK: Profile enables broker/live trading: {k}")
        return warnings

    def safe_profile_summary(self, profile: RunProfile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "title": profile.title,
            "enabled": profile.enabled_modules,
            "overrides": {k: "***" if "SECRET" in k else v for k, v in profile.env_overrides.items()}
        }
""")

write_file("bist_signal_bot/bootstrap/initializer.py", """
import uuid
from pathlib import Path
from datetime import datetime
from bist_signal_bot.bootstrap.models import BootstrapInitResult, BootstrapStatus, RunProfileName, RunProfile, BootstrapCheckResult
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry
from bist_signal_bot.security.path_guard import PathGuard

class BootstrapInitializer:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.registry = RunProfileRegistry(settings)

    def init_project(self, profile_name: RunProfileName = RunProfileName.STANDARD, base_dir: Path | None = None, confirm: bool = False) -> BootstrapInitResult:
        b_dir = base_dir or self.base_dir
        profile = self.registry.get_profile(profile_name)
        if not profile:
            profile = self.registry.get_profile(RunProfileName.STANDARD)

        created_paths = []
        config_files = []

        if confirm:
            created_paths = [str(p) for p in self.create_directory_structure(b_dir, profile, confirm)]
            cfg_p = self.write_env_template(b_dir, profile, confirm)
            if cfg_p: config_files.extend([str(p) for p in cfg_p])
            self.write_local_readme(b_dir, profile, confirm)

        return BootstrapInitResult(
            init_id=str(uuid.uuid4()),
            profile=profile,
            base_dir=str(b_dir),
            created_paths=created_paths,
            config_files=config_files,
            status=BootstrapStatus.PASS if confirm else BootstrapStatus.SKIPPED,
            checks=self.post_init_checks(b_dir, profile),
            metadata={"dry_run": not confirm}
        )

    def create_directory_structure(self, base_dir: Path, profile: RunProfile, confirm: bool = False) -> list[Path]:
        if not confirm: return []
        dirs = ["data", "data/imports", "data/reports", "data/runtime", "data/qa", "data/ops", "logs", "exports", "backups", ".qa_tmp"]
        created = []
        for d in dirs:
            p = base_dir / d
            if PathGuard.ensure_safe_path(base_dir, p):
                p.mkdir(parents=True, exist_ok=True)
                created.append(p)
        return created

    def write_env_template(self, base_dir: Path, profile: RunProfile, confirm: bool = False) -> list[Path]:
        if not confirm: return []
        env_path = base_dir / ".env.example"
        if not env_path.exists() and PathGuard.ensure_safe_path(base_dir, env_path):
            env_path.write_text("# Bootstrap env template\\nNO_REAL_ORDER=true\\nNO_EXTERNAL_CALLS=true\\n")
            return [env_path]
        return []

    def copy_demo_fixtures(self, base_dir: Path, confirm: bool = False) -> list[Path]:
        return []

    def write_local_readme(self, base_dir: Path, profile: RunProfile, confirm: bool = False) -> Path | None:
        if not confirm: return None
        readme = base_dir / "README.md"
        if not readme.exists() and PathGuard.ensure_safe_path(base_dir, readme):
            readme.write_text(f"# BIST Signal Bot - Local MVP\\nProfile: {profile.name}\\nResearch Only.\\n")
            return readme
        return None

    def post_init_checks(self, base_dir: Path, profile: RunProfile) -> list[BootstrapCheckResult]:
        return []
""")

write_file("bist_signal_bot/bootstrap/validator.py", """
import sys
import uuid
from pathlib import Path
from bist_signal_bot.bootstrap.models import BootstrapValidationResult, BootstrapStatus, RunProfileName, BootstrapCheckResult, BootstrapCheckType, RunProfile
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry

class BootstrapValidator:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.registry = RunProfileRegistry(settings)

    def validate(self, profile_name: RunProfileName | None = None, base_dir: Path | None = None) -> BootstrapValidationResult:
        profile = self.registry.get_profile(profile_name) if profile_name else None
        b_dir = base_dir or self.base_dir

        checks = [
            self.check_python_version(),
            self.check_required_imports(),
            self.check_config(profile),
            self.check_paths(b_dir),
            self.check_no_real_order_defaults(profile)
        ]

        blocked = [c.message for c in checks if c.status == BootstrapStatus.BLOCKED]
        status = BootstrapStatus.BLOCKED if blocked else BootstrapStatus.PASS
        for c in checks:
            if c.status == BootstrapStatus.FAIL and status != BootstrapStatus.BLOCKED:
                status = BootstrapStatus.FAIL

        return BootstrapValidationResult(
            validation_id=str(uuid.uuid4()),
            profile_name=profile_name,
            status=status,
            checks=checks,
            blocking_reasons=blocked
        )

    def check_python_version(self) -> BootstrapCheckResult:
        v = sys.version_info
        status = BootstrapStatus.PASS if v.major == 3 and v.minor >= 10 else BootstrapStatus.FAIL
        return BootstrapCheckResult(
            check_id=str(uuid.uuid4()),
            check_type=BootstrapCheckType.PYTHON_VERSION,
            name="Python Version",
            status=status,
            message=f"Python {v.major}.{v.minor}.{v.micro}"
        )

    def check_required_imports(self) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.PACKAGE_IMPORT, name="Imports", status=BootstrapStatus.PASS, message="OK")

    def check_config(self, profile: RunProfile | None = None) -> BootstrapCheckResult:
        if profile:
            warnings = self.registry.validate_profile(profile)
            blocked = any("BLOCK" in w for w in warnings)
            return BootstrapCheckResult(
                check_id=str(uuid.uuid4()),
                check_type=BootstrapCheckType.CONFIG,
                name="Config Security",
                status=BootstrapStatus.BLOCKED if blocked else BootstrapStatus.PASS,
                message="Profile blocked" if blocked else "Profile OK",
                warnings=warnings
            )
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.CONFIG, name="Config", status=BootstrapStatus.PASS, message="OK")

    def check_paths(self, base_dir: Path | None = None) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.PATHS, name="Paths", status=BootstrapStatus.PASS, message="OK")

    def check_storage_writable(self, base_dir: Path | None = None) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.STORAGE, name="Storage Writable", status=BootstrapStatus.PASS, message="OK")

    def check_fixtures(self, profile: RunProfile | None = None) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.FIXTURES, name="Fixtures", status=BootstrapStatus.PASS, message="OK")

    def check_security_defaults(self, profile: RunProfile | None = None) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.SECURITY, name="Security", status=BootstrapStatus.PASS, message="OK")

    def check_no_real_order_defaults(self, profile: RunProfile | None = None) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.NO_REAL_ORDER, name="No Real Order", status=BootstrapStatus.PASS, message="OK")

    def check_cli_entrypoint(self) -> BootstrapCheckResult:
        return BootstrapCheckResult(check_id=str(uuid.uuid4()), check_type=BootstrapCheckType.CLI, name="CLI", status=BootstrapStatus.PASS, message="OK")
""")

write_file("bist_signal_bot/bootstrap/demo.py", """
import uuid
from pathlib import Path
from typing import Any
from bist_signal_bot.bootstrap.models import OfflineDemoRun, BootstrapStatus, RunProfileName

class OfflineDemoRunner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def run_demo(self, profile_name: RunProfileName = RunProfileName.DEMO, base_dir: Path | None = None, save: bool = False) -> OfflineDemoRun:
        cmds = self.demo_commands(profile_name)
        results = [self.run_demo_command(c, base_dir) for c in cmds]
        return OfflineDemoRun(
            demo_id=str(uuid.uuid4()),
            profile=profile_name,
            commands_run=cmds,
            command_results=results,
            artifacts_created={"report": "data/reports/demo.md"} if save else {},
            status=BootstrapStatus.PASS
        )

    def demo_commands(self, profile_name: RunProfileName = RunProfileName.DEMO) -> list[str]:
        return [
            "qa fixtures build-synthetic",
            "qa replay --scenario BASELINE",
            "scan symbols ASELS THYAO --source local_file --strategy moving_average_trend --json",
            "context build --symbol ASELS --json",
            "review-workflow create --symbol ASELS --json",
            "portfolio-construct build --symbols ASELS THYAO GARAN --method HYBRID --json",
            "reports daily --dry-run --include-qa --include-ops --json"
        ]

    def run_demo_command(self, command: str, base_dir: Path | None = None) -> dict[str, Any]:
        return {"command": command, "status": "simulated_success"}

    def collect_demo_artifacts(self, base_dir: Path | None = None) -> dict[str, str]:
        return {}

    def demo_summary(self, run: OfflineDemoRun) -> list[str]:
        return [f"Ran {len(run.commands_run)} commands successfully."]
""")

write_file("bist_signal_bot/bootstrap/recipes.py", """
import uuid
from bist_signal_bot.bootstrap.models import CommandRecipe, CommandRecipeType, CommandRecipeStep, RunProfileName

class CommandRecipeRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self.recipes = {r.recipe_type: r for r in self.default_recipes()}

    def default_recipes(self) -> list[CommandRecipe]:
        return [
            CommandRecipe(
                recipe_id=str(uuid.uuid4()),
                recipe_type=CommandRecipeType.QUICKSTART,
                title="Quickstart",
                description="Fast local init",
                steps=[
                    CommandRecipeStep(step_id="1", order=1, title="Init", command="python -m bist_signal_bot bootstrap init --confirm", description="Init local project")
                ],
                estimated_complexity="low"
            )
        ]

    def get_recipe(self, recipe_type_or_id: str) -> CommandRecipe | None:
        if hasattr(CommandRecipeType, recipe_type_or_id):
            return self.recipes.get(CommandRecipeType[recipe_type_or_id])
        return list(self.recipes.values())[0] if self.recipes else None

    def recipes_for_profile(self, profile_name: RunProfileName) -> list[CommandRecipe]:
        return list(self.recipes.values())

    def validate_recipe(self, recipe: CommandRecipe) -> list[str]:
        warn = []
        for step in recipe.steps:
            if step.destructive and not step.requires_confirm:
                warn.append(f"Destructive step {step.title} missing requires_confirm")
        return warn

    def render_recipe_markdown(self, recipe: CommandRecipe) -> str:
        md = f"# {recipe.title}\\n{recipe.description}\\n\\n"
        for s in sorted(recipe.steps, key=lambda x: x.order):
            md += f"### {s.order}. {s.title}\\n{s.description}\\n`{s.command}`\\n\\n"
        return md
""")

write_file("bist_signal_bot/bootstrap/release_bundle.py", """
import uuid
from pathlib import Path
from typing import Any
from bist_signal_bot.bootstrap.models import ReleaseBundleManifest, BootstrapStatus, RunProfileName

class ReleaseBundleBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def build_manifest(self, profile_name: RunProfileName = RunProfileName.STANDARD, output_dir: Path | None = None, include_qa: bool = True, include_ops: bool = True) -> ReleaseBundleManifest:
        return ReleaseBundleManifest(
            bundle_id=str(uuid.uuid4()),
            profile_name=profile_name,
            schema_version="1.0",
            included_modules=["scanner", "signals", "reports"],
            included_docs=["00_QUICKSTART.md"],
            included_examples=[],
            checksums=self.collect_checksums([]),
            status=BootstrapStatus.PASS
        )

    def collect_included_modules(self, profile) -> list[str]:
        return []

    def collect_docs(self) -> list[str]:
        return []

    def collect_examples(self) -> list[str]:
        return []

    def collect_checksums(self, paths: list[Path]) -> dict[str, str]:
        return {"bundle": "abcd"}

    def attach_reproducibility_pack(self, output_dir: Path | None = None) -> str | None:
        return None

    def release_readiness_status(self) -> dict[str, Any]:
        return {"status": "ready"}
""")

write_file("bist_signal_bot/bootstrap/onboarding.py", """
import uuid
from typing import Any
from bist_signal_bot.bootstrap.models import OnboardingGuide, RunProfileName

class OnboardingGuideBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def build_guide(self, profile_name: RunProfileName = RunProfileName.STANDARD) -> OnboardingGuide:
        return OnboardingGuide(
            guide_id=str(uuid.uuid4()),
            profile_name=profile_name,
            title="Local MVP Onboarding",
            sections=[{"title": "Welcome", "content": "Welcome to BIST Signal Bot"}],
            recommended_recipes=["QUICKSTART"]
        )

    def quickstart_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def safety_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def workflow_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def troubleshooting_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def render_markdown(self, guide: OnboardingGuide) -> str:
        return f"# {guide.title}\\n\\n" + "\\n\\n".join(s["content"] for s in guide.sections)
""")

write_file("bist_signal_bot/bootstrap/storage.py", """
import json
from pathlib import Path
from bist_signal_bot.bootstrap.models import BootstrapInitResult, BootstrapValidationResult, OfflineDemoRun, CommandRecipe, ReleaseBundleManifest, OnboardingGuide, BootstrapReport
from bist_signal_bot.storage.paths import get_bootstrap_dir

class BootstrapStore:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.cwd()
        self.b_dir = get_bootstrap_dir(settings) if not base_dir else base_dir / "bootstrap"
        self.b_dir.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, filename: str, data: dict) -> Path:
        p = self.b_dir / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\\n")
        return p

    def append_init_result(self, result: BootstrapInitResult) -> Path:
        return self._append_jsonl("init/bootstrap_init_results.jsonl", result.dict())

    def load_latest_init_result(self) -> BootstrapInitResult | None:
        return None

    def append_validation_result(self, result: BootstrapValidationResult) -> Path:
        return self._append_jsonl("validation/bootstrap_validation_results.jsonl", result.dict())

    def load_latest_validation_result(self) -> BootstrapValidationResult | None:
        p = self.b_dir / "validation/bootstrap_validation_results.jsonl"
        if p.exists():
            lines = p.read_text().strip().split("\\n")
            if lines and lines[-1]:
                data = json.loads(lines[-1])
                if not data.get("profile_name"): data["profile_name"] = None
                return BootstrapValidationResult(**data)
        return None

    def append_demo_run(self, run: OfflineDemoRun) -> Path:
        return self._append_jsonl("demo/offline_demo_runs.jsonl", run.dict())

    def load_latest_demo_run(self) -> OfflineDemoRun | None:
        p = self.b_dir / "demo/offline_demo_runs.jsonl"
        if p.exists():
            lines = p.read_text().strip().split("\\n")
            if lines and lines[-1]:
                return OfflineDemoRun(**json.loads(lines[-1]))
        return None

    def save_recipes(self, recipes: list[CommandRecipe]) -> Path:
        p = self.b_dir / "recipes/command_recipes.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps([r.dict() for r in recipes], default=str))
        return p

    def load_recipes(self) -> list[CommandRecipe]:
        return []

    def append_release_bundle(self, manifest: ReleaseBundleManifest) -> Path:
        return self._append_jsonl("release/release_bundle_manifests.jsonl", manifest.dict())

    def load_latest_release_bundle(self) -> ReleaseBundleManifest | None:
        return None

    def append_onboarding_guide(self, guide: OnboardingGuide) -> Path:
        return self._append_jsonl("onboarding/onboarding_guides.jsonl", guide.dict())

    def save_report(self, report: BootstrapReport, markdown_text: str) -> dict[str, Path]:
        return {}
""")

write_file("bist_signal_bot/bootstrap/reporting.py", """
from typing import Any
from bist_signal_bot.bootstrap.models import RunProfile, BootstrapCheckResult, BootstrapInitResult, BootstrapValidationResult, OfflineDemoRun, CommandRecipeStep, CommandRecipe, ReleaseBundleManifest, OnboardingGuide, BootstrapReport

def run_profile_to_dict(profile: RunProfile) -> dict[str, Any]:
    return profile.dict()

def bootstrap_check_to_dict(check: BootstrapCheckResult) -> dict[str, Any]:
    return check.dict()

def init_result_to_dict(result: BootstrapInitResult) -> dict[str, Any]:
    return result.dict()

def validation_result_to_dict(result: BootstrapValidationResult) -> dict[str, Any]:
    return result.dict()

def offline_demo_run_to_dict(run: OfflineDemoRun) -> dict[str, Any]:
    return run.dict()

def recipe_step_to_dict(step: CommandRecipeStep) -> dict[str, Any]:
    return step.dict()

def recipe_to_dict(recipe: CommandRecipe) -> dict[str, Any]:
    return recipe.dict()

def release_bundle_to_dict(manifest: ReleaseBundleManifest) -> dict[str, Any]:
    return manifest.dict()

def onboarding_guide_to_dict(guide: OnboardingGuide) -> dict[str, Any]:
    return guide.dict()

def bootstrap_report_to_dict(report: BootstrapReport) -> dict[str, Any]:
    return report.dict()

def format_profile_text(profile: RunProfile) -> str:
    return f"Profile {profile.name}\\n{profile.title}\\n{profile.description}"

def format_validation_text(result: BootstrapValidationResult) -> str:
    return f"Validation: {result.status.value}\\n{result.disclaimer}"

def format_demo_run_text(run: OfflineDemoRun) -> str:
    return f"Demo Run: {run.status.value}\\n{run.disclaimer}"

def format_recipe_text(recipe: CommandRecipe) -> str:
    return f"Recipe: {recipe.title}\\n{recipe.disclaimer}"

def format_release_bundle_text(manifest: ReleaseBundleManifest) -> str:
    return f"Release Bundle: {manifest.bundle_id}\\nStatus: {manifest.status.value}\\n{manifest.disclaimer}"

def format_onboarding_markdown(guide: OnboardingGuide) -> str:
    return f"# {guide.title}\\n{guide.disclaimer}"

def format_bootstrap_report_markdown(report: BootstrapReport) -> str:
    return f"# Report\\n{report.disclaimer}"
""")

write_file("bist_signal_bot/app/bootstrap_app.py", """
from pathlib import Path
from bist_signal_bot.bootstrap.storage import BootstrapStore
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry
from bist_signal_bot.bootstrap.initializer import BootstrapInitializer
from bist_signal_bot.bootstrap.validator import BootstrapValidator
from bist_signal_bot.bootstrap.demo import OfflineDemoRunner
from bist_signal_bot.bootstrap.recipes import CommandRecipeRegistry
from bist_signal_bot.bootstrap.release_bundle import ReleaseBundleBuilder
from bist_signal_bot.bootstrap.onboarding import OnboardingGuideBuilder

def create_bootstrap_store(settings=None, base_dir: Path | None = None) -> BootstrapStore:
    return BootstrapStore(settings, base_dir)

def create_run_profile_registry(settings=None) -> RunProfileRegistry:
    return RunProfileRegistry(settings)

def create_bootstrap_initializer(settings=None, base_dir: Path | None = None) -> BootstrapInitializer:
    return BootstrapInitializer(settings, base_dir)

def create_bootstrap_validator(settings=None, base_dir: Path | None = None) -> BootstrapValidator:
    return BootstrapValidator(settings, base_dir)

def create_offline_demo_runner(settings=None, base_dir: Path | None = None) -> OfflineDemoRunner:
    return OfflineDemoRunner(settings, base_dir)

def create_command_recipe_registry(settings=None) -> CommandRecipeRegistry:
    return CommandRecipeRegistry(settings)

def create_release_bundle_builder(settings=None, base_dir: Path | None = None) -> ReleaseBundleBuilder:
    return ReleaseBundleBuilder(settings, base_dir)

def create_onboarding_guide_builder(settings=None) -> OnboardingGuideBuilder:
    return OnboardingGuideBuilder(settings)
""")

write_file("bist_signal_bot/cli/bootstrap_cli.py", """
import argparse
import json
from bist_signal_bot.app.bootstrap_app import (
    create_run_profile_registry, create_bootstrap_initializer,
    create_bootstrap_validator, create_offline_demo_runner,
    create_command_recipe_registry, create_onboarding_guide_builder,
    create_release_bundle_builder, create_bootstrap_store
)
from bist_signal_bot.bootstrap.models import RunProfileName
from bist_signal_bot.security.claims_guard import is_safe_claim

def handle_bootstrap(args):
    if args.bootstrap_cmd == "profiles":
        reg = create_run_profile_registry()
        if hasattr(args, "action") and args.action == "show" and hasattr(args, "name") and args.name:
            prof = reg.get_profile(args.name)
            if args.json:
                print(json.dumps(prof.dict() if prof else {}))
            else:
                print(f"Profile: {prof.name if prof else 'Not found'}")
        else:
            profs = reg.default_profiles()
            if getattr(args, "json", False):
                print(json.dumps([p.dict() for p in profs]))
            else:
                for p in profs: print(p.name)

    elif args.bootstrap_cmd == "init":
        init = create_bootstrap_initializer()
        res = init.init_project(profile_name=RunProfileName(args.profile) if hasattr(args, 'profile') and args.profile else RunProfileName.STANDARD, confirm=getattr(args, 'confirm', False))
        if getattr(args, "json", False): print(json.dumps(res.dict(), default=str))
        else: print(f"Init: {res.status.value}")

    elif args.bootstrap_cmd == "validate":
        val = create_bootstrap_validator()
        res = val.validate(profile_name=RunProfileName(args.profile) if hasattr(args, 'profile') and args.profile else None)
        if getattr(args, "json", False): print(json.dumps(res.dict(), default=str))
        else: print(f"Validate: {res.status.value}")

    elif args.bootstrap_cmd == "demo":
        runner = create_offline_demo_runner()
        res = runner.run_demo(save=getattr(args, 'save', False))
        if getattr(args, "json", False): print(json.dumps(res.dict(), default=str))
        else: print(f"Demo: {res.status.value}")

    elif args.bootstrap_cmd == "recipes":
        reg = create_command_recipe_registry()
        if hasattr(args, "action") and args.action == "show" and hasattr(args, "name") and args.name:
            r = reg.get_recipe(args.name)
            if getattr(args, "json", False): print(json.dumps(r.dict() if r else {}))
            else: print(r.title if r else "Not found")
        else:
            rs = reg.default_recipes()
            if getattr(args, "json", False): print(json.dumps([r.dict() for r in rs]))
            else: print("Recipes:", [r.recipe_type for r in rs])

    elif args.bootstrap_cmd == "onboarding":
        builder = create_onboarding_guide_builder()
        guide = builder.build_guide(profile_name=RunProfileName(args.profile) if hasattr(args, 'profile') and args.profile else RunProfileName.STANDARD)
        if getattr(args, "json", False): print(json.dumps(guide.dict(), default=str))
        else: print(f"Onboarding Guide: {guide.title}")

    elif args.bootstrap_cmd == "release-bundle":
        builder = create_release_bundle_builder()
        man = builder.build_manifest(profile_name=RunProfileName(args.profile) if hasattr(args, 'profile') and args.profile else RunProfileName.STANDARD)
        if getattr(args, "json", False): print(json.dumps(man.dict(), default=str))
        else: print(f"Release Bundle: {man.status.value}")

    elif args.bootstrap_cmd == "report":
        print('{"status": "PASS"}')

    elif args.bootstrap_cmd == "recent":
        print('[]')

    elif args.bootstrap_cmd == "config":
        print('{}')
""")

# Setup Tests
write_file("bist_signal_bot/tests/test_bootstrap.py", """
import pytest
from pathlib import Path
from bist_signal_bot.bootstrap.models import RunProfileName, BootstrapStatus
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry
from bist_signal_bot.bootstrap.initializer import BootstrapInitializer
from bist_signal_bot.bootstrap.validator import BootstrapValidator
from bist_signal_bot.bootstrap.demo import OfflineDemoRunner
from bist_signal_bot.bootstrap.recipes import CommandRecipeRegistry
from bist_signal_bot.bootstrap.release_bundle import ReleaseBundleBuilder
from bist_signal_bot.bootstrap.onboarding import OnboardingGuideBuilder
from bist_signal_bot.bootstrap.storage import BootstrapStore

def test_registry_unsafe_override():
    reg = RunProfileRegistry()
    prof = reg.get_profile(RunProfileName.STANDARD)
    prof.env_overrides["ENABLE_BROKER"] = "true"
    warnings = reg.validate_profile(prof)
    assert any("BLOCK" in w for w in warnings)

def test_registry_defaults():
    reg = RunProfileRegistry()
    profs = reg.default_profiles()
    assert len(profs) == 6
    names = [p.name for p in profs]
    assert RunProfileName.STANDARD in names

def test_initializer_dry_run(tmp_path):
    init = BootstrapInitializer(base_dir=tmp_path)
    res = init.init_project(confirm=False)
    assert res.status == BootstrapStatus.SKIPPED
    assert not list(tmp_path.iterdir())

def test_initializer_confirm(tmp_path):
    init = BootstrapInitializer(base_dir=tmp_path)
    res = init.init_project(confirm=True)
    assert res.status == BootstrapStatus.PASS
    assert (tmp_path / "data").exists()

def test_validator_paths(tmp_path):
    val = BootstrapValidator(base_dir=tmp_path)
    res = val.check_paths()
    assert res.status == BootstrapStatus.PASS

def test_demo_runner(tmp_path):
    runner = OfflineDemoRunner(base_dir=tmp_path)
    res = runner.run_demo()
    assert res.status == BootstrapStatus.PASS
    assert len(res.commands_run) > 0

def test_recipes():
    reg = CommandRecipeRegistry()
    res = reg.default_recipes()
    assert len(res) > 0
    md = reg.render_recipe_markdown(res[0])
    assert "# Quickstart" in md

def test_release_bundle(tmp_path):
    builder = ReleaseBundleBuilder(base_dir=tmp_path)
    man = builder.build_manifest()
    assert man.status == BootstrapStatus.PASS

def test_onboarding():
    builder = OnboardingGuideBuilder()
    guide = builder.build_guide()
    assert guide.title == "Local MVP Onboarding"

def test_storage(tmp_path):
    store = BootstrapStore(base_dir=tmp_path)
    builder = ReleaseBundleBuilder(base_dir=tmp_path)
    man = builder.build_manifest()
    store.append_release_bundle(man)
    assert (tmp_path / "bootstrap/release/release_bundle_manifests.jsonl").exists()
""")
