import uuid
from pathlib import Path
from typing import List, Optional

from bist_signal_bot.deployment.models import (
    EnvTemplateRequest,
    EnvTemplateResult,
    DeploymentProfile,
    DeploymentStatus
)

class EnvTemplateBuilder:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def build_template(self, request: EnvTemplateRequest, profile: DeploymentProfile) -> EnvTemplateResult:
        result = EnvTemplateResult(
            result_id=str(uuid.uuid4()),
            status=DeploymentStatus.UNKNOWN,
            output_path=request.output_path
        )

        try:
            text = self.render_env_text(
                profile=profile,
                include_comments=request.include_comments,
                include_placeholders=request.include_placeholders
            )

            if request.output_path:
                out_path = Path(request.output_path)
                if not out_path.is_absolute():
                    out_path = self.base_dir / out_path

                if out_path.exists() and not request.overwrite:
                    result.status = DeploymentStatus.SKIPPED
                    result.skipped_existing = True
                    result.warnings.append(f"File {out_path} already exists. Skipped.")
                    return result

            result.status = DeploymentStatus.PASS
            result.metadata["generated_text"] = text
            result.variables_written = len(self.safe_variable_lines(profile))
        except Exception as e:
            result.status = DeploymentStatus.FAIL
            result.errors.append(str(e))

        return result

    def render_env_text(self, profile: DeploymentProfile, include_comments: bool = True, include_placeholders: bool = True) -> str:
        lines = []
        if include_comments:
            lines.append("# BIST Signal Bot - Environment Template")
            lines.append(f"# Profile: {profile.name}")
            lines.append(f"# {profile.description}")
            lines.append("# " + "-" * 40)
            lines.append("")

        lines.extend(self.safe_variable_lines(profile))

        if include_placeholders:
            if include_comments:
                lines.append("\n# Integrations (Placeholders - DO NOT commit real secrets)")
            lines.append("TELEGRAM_BOT_TOKEN=")
            lines.append("TELEGRAM_ALLOWED_CHAT_IDS=")
            lines.append("OPENAI_API_KEY=")
            lines.append("ANTHROPIC_API_KEY=")

        return "\n".join(lines)

    def safe_variable_lines(self, profile: DeploymentProfile) -> List[str]:
        lines = []
        # Emit standard safe profile overrides
        for k, v in profile.settings_overrides.items():
            if isinstance(v, bool):
                val = "true" if v else "false"
            else:
                val = str(v)
            lines.append(f"{k}={val}")
        return lines

    def write_env_file(self, text: str, output_path: Path, overwrite: bool = False, confirm: bool = False) -> Path:
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"{output_path} already exists. Set overwrite=True to overwrite.")

        if output_path.exists() and overwrite and not confirm:
            raise ValueError(f"Overwriting {output_path} requires confirm=True.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        return output_path
