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
        md = f"# {recipe.title}\n{recipe.description}\n\n"
        for s in sorted(recipe.steps, key=lambda x: x.order):
            md += f"### {s.order}. {s.title}\n{s.description}\n`{s.command}`\n\n"
        return md

# Adding mock recipes to the existing recipes mapping if it exists, otherwise just declare them
def add_research_orchestrator_recipes(recipes_dict: dict):
    recipes_dict["quick_research_scan_campaign"] = {
        "command": "python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --symbols ASELS THYAO --dry-run",
        "description": "Run a quick research scan using the Orchestrator."
    }
    recipes_dict["full_research_pipeline_dry_run"] = {
        "command": "python -m bist_signal_bot orchestrator run --campaign FULL_RESEARCH_PIPELINE --symbols ASELS THYAO --dry-run",
        "description": "Run the full research pipeline safely in dry-run mode."
    }
    recipes_dict["qa_ops_release_campaign"] = {
        "command": "python -m bist_signal_bot orchestrator run --campaign QA_OPS_RELEASE_CHECK --dry-run",
        "description": "Run the release check QA and Ops campaign via Orchestrator."
    }
