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
    return f"Profile {profile.name}\n{profile.title}\n{profile.description}"

def format_validation_text(result: BootstrapValidationResult) -> str:
    return f"Validation: {result.status.value}\n{result.disclaimer}"

def format_demo_run_text(run: OfflineDemoRun) -> str:
    return f"Demo Run: {run.status.value}\n{run.disclaimer}"

def format_recipe_text(recipe: CommandRecipe) -> str:
    return f"Recipe: {recipe.title}\n{recipe.disclaimer}"

def format_release_bundle_text(manifest: ReleaseBundleManifest) -> str:
    return f"Release Bundle: {manifest.bundle_id}\nStatus: {manifest.status.value}\n{manifest.disclaimer}"

def format_onboarding_markdown(guide: OnboardingGuide) -> str:
    return f"# {guide.title}\n{guide.disclaimer}"

def format_bootstrap_report_markdown(report: BootstrapReport) -> str:
    return f"# Report\n{report.disclaimer}"
