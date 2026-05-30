from typing import Any, List
from bist_signal_bot.cli_ux.models import WorkflowRun
from bist_signal_bot.cli_ux.workflow_runner import CLIWorkflowRunner

class CommandRecipeExecutor:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self.runner = CLIWorkflowRunner(settings, base_dir)

    def execute_recipe(self, recipe_id_or_type: str, dry_run: bool = True, save: bool = False) -> WorkflowRun:
        commands = self.preview_recipe(recipe_id_or_type)
        return self.runner.run_workflow(
            name=f"Recipe_{recipe_id_or_type}",
            commands=commands,
            dry_run=dry_run,
            save=save
        )

    def recipe_to_commands(self, recipe: Any) -> List[str]:
        # Simple mock for converting recipe objects to commands
        if hasattr(recipe, 'steps'):
            return [step.command for step in recipe.steps]
        return []

    def validate_recipe_execution(self, recipe: Any) -> List[str]:
        commands = self.recipe_to_commands(recipe)
        return self.runner.validate_commands(commands)

    def preview_recipe(self, recipe_id_or_type: str) -> List[str]:
        # Mock implementations of recipes
        if recipe_id_or_type == "QUICKSTART":
            return [
                "python -m bist_signal_bot healthcheck",
                "python -m bist_signal_bot scan symbols"
            ]
        elif recipe_id_or_type == "OFFLINE_DEMO":
            return [
                "python -m bist_signal_bot config show",
                "python -m bist_signal_bot scan symbols --limit 5"
            ]
        else:
            return [f"echo 'Unknown recipe {recipe_id_or_type}'"]
