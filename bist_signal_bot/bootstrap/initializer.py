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
            env_path.write_text("# Bootstrap env template\nNO_REAL_ORDER=true\nNO_EXTERNAL_CALLS=true\n")
            return [env_path]
        return []

    def copy_demo_fixtures(self, base_dir: Path, confirm: bool = False) -> list[Path]:
        return []

    def write_local_readme(self, base_dir: Path, profile: RunProfile, confirm: bool = False) -> Path | None:
        if not confirm: return None
        readme = base_dir / "README.md"
        if not readme.exists() and PathGuard.ensure_safe_path(base_dir, readme):
            readme.write_text(f"# BIST Signal Bot - Local MVP\nProfile: {profile.name}\nResearch Only.\n")
            return readme
        return None

    def post_init_checks(self, base_dir: Path, profile: RunProfile) -> list[BootstrapCheckResult]:
        return []
