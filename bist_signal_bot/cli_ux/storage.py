import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from bist_signal_bot.cli_ux.models import (
    CLICommandContract, CLIOutputSchema, CLIAlias,
    WorkflowRun, CLICompatibilityResult, CLIUXReport
)
from bist_signal_bot.storage.paths import get_cli_ux_dir

class CLIUXStore:
    def __init__(self, settings=None, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_cli_ux_dir(settings)

        self.contracts_file = self.base_dir / "contracts" / "cli_command_contracts.json"
        self.schemas_file = self.base_dir / "schemas" / "cli_output_schemas.json"
        self.aliases_file = self.base_dir / "aliases" / "cli_aliases.json"
        self.workflows_file = self.base_dir / "workflows" / "workflow_runs.jsonl"
        self.compatibility_file = self.base_dir / "compatibility" / "cli_compatibility_results.jsonl"

        self.reports_dir = self.base_dir / "reports"

        self._init_dirs()

    def _init_dirs(self):
        self.contracts_file.parent.mkdir(parents=True, exist_ok=True)
        self.schemas_file.parent.mkdir(parents=True, exist_ok=True)
        self.aliases_file.parent.mkdir(parents=True, exist_ok=True)
        self.workflows_file.parent.mkdir(parents=True, exist_ok=True)
        self.compatibility_file.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_contracts(self, contracts: List[CLICommandContract]) -> Path:
        data = [c.dict() for c in contracts]
        with open(self.contracts_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.contracts_file

    def load_contracts(self) -> List[CLICommandContract]:
        if not self.contracts_file.exists():
            return []
        with open(self.contracts_file, "r") as f:
            data = json.load(f)
        return [CLICommandContract(**d) for d in data]

    def save_schemas(self, schemas: List[CLIOutputSchema]) -> Path:
        data = [s.dict(by_alias=True) for s in schemas]
        with open(self.schemas_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.schemas_file

    def load_schemas(self) -> List[CLIOutputSchema]:
        if not self.schemas_file.exists():
            return []
        with open(self.schemas_file, "r") as f:
            data = json.load(f)
        return [CLIOutputSchema(**d) for d in data]

    def save_aliases(self, aliases: List[CLIAlias]) -> Path:
        data = [a.dict() for a in aliases]
        with open(self.aliases_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.aliases_file

    def load_aliases(self) -> List[CLIAlias]:
        if not self.aliases_file.exists():
            return []
        with open(self.aliases_file, "r") as f:
            data = json.load(f)
        return [CLIAlias(**d) for d in data]

    def append_workflow_run(self, run: WorkflowRun) -> Path:
        # Convert datetime for JSON serialization
        d = run.dict()
        d['created_at'] = d['created_at'].isoformat()
        for step in d['steps']:
            step['started_at'] = step['started_at'].isoformat()
            if step['finished_at']:
                step['finished_at'] = step['finished_at'].isoformat()
        d['status'] = d['status'].value
        for step in d['steps']:
            step['status'] = step['status'].value

        with open(self.workflows_file, "a") as f:
            f.write(json.dumps(d) + "\n")
        return self.workflows_file

    def load_workflow_runs(self, limit: int = 1000) -> List[WorkflowRun]:
        if not self.workflows_file.exists():
            return []
        runs = []
        with open(self.workflows_file, "r") as f:
            lines = f.readlines()[-limit:]
            for line in lines:
                if line.strip():
                    try:
                        d = json.loads(line)
                        runs.append(WorkflowRun(**d))
                    except Exception:
                        pass
        return runs

    def append_compatibility_result(self, result: CLICompatibilityResult) -> Path:
        d = result.dict()
        d['created_at'] = d['created_at'].isoformat()
        d['status'] = d['status'].value
        with open(self.compatibility_file, "a") as f:
            f.write(json.dumps(d) + "\n")
        return self.compatibility_file

    def load_latest_compatibility(self) -> Optional[CLICompatibilityResult]:
        if not self.compatibility_file.exists():
            return None
        with open(self.compatibility_file, "r") as f:
            lines = f.readlines()
            if not lines:
                return None
            last_line = lines[-1].strip()
            if not last_line:
                return None
            return CLICompatibilityResult(**json.loads(last_line))

    def save_report(self, report: CLIUXReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_file = report_dir / "cli_ux_report.md"
        with open(md_file, "w") as f:
            f.write(markdown_text)

        json_file = report_dir / "cli_ux_report.json"
        d = report.dict()
        d['generated_at'] = d['generated_at'].isoformat()
        if d.get('compatibility'):
            d['compatibility']['created_at'] = d['compatibility']['created_at'].isoformat()
            d['compatibility']['status'] = d['compatibility']['status'].value
        with open(json_file, "w") as f:
            json.dump(d, f, indent=2, default=str)

        return {"markdown": md_file, "json": json_file}
