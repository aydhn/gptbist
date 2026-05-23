import pytest
from pathlib import Path
from bist_signal_bot.deployment.env_template import EnvTemplateBuilder
from bist_signal_bot.deployment.models import EnvTemplateRequest, DeploymentProfileType
from bist_signal_bot.deployment.profiles import DeploymentProfileManager

def test_env_template_builder_placeholders(tmp_path):
    builder = EnvTemplateBuilder(base_dir=tmp_path)
    manager = DeploymentProfileManager()
    profile = manager.get_profile(DeploymentProfileType.RESEARCH_ONLY)

    req = EnvTemplateRequest(profile_type=DeploymentProfileType.RESEARCH_ONLY)
    result = builder.build_template(req, profile)

    text = result.metadata["generated_text"]
    assert "TELEGRAM_BOT_TOKEN=" in text
    assert "OPENAI_API_KEY=" in text
    assert "FORCE_RESEARCH_ONLY=true" in text

def test_env_template_write_requires_confirm(tmp_path):
    builder = EnvTemplateBuilder(base_dir=tmp_path)
    out_file = tmp_path / ".env.test"
    out_file.write_text("existing content")

    with pytest.raises(ValueError, match="requires confirm=True"):
        builder.write_env_file("new content", out_file, overwrite=True, confirm=False)

def test_env_template_write_success(tmp_path):
    builder = EnvTemplateBuilder(base_dir=tmp_path)
    out_file = tmp_path / ".env.test"
    out_file.write_text("existing content")

    builder.write_env_file("new content", out_file, overwrite=True, confirm=True)
    assert out_file.read_text() == "new content"
