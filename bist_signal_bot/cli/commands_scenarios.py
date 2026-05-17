import click
import json
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.scenarios_app import create_scenario_runner, create_scenario_registry, create_scenario_store
from bist_signal_bot.scenarios.reporting import scenario_result_to_dict

@click.group(name="scenario", help="End-to-end scenario runner and acceptance workflows.")
def scenario_cli():
    pass

@scenario_cli.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def list_scenarios(json_output):
    """List available scenarios."""
    registry = create_scenario_registry(Settings())
    scenarios = registry.list_scenarios()

    if json_output:
        click.echo(json.dumps([s.model_dump(mode='json') for s in scenarios], indent=2))
        return

    click.echo(f"Found {len(scenarios)} scenarios:\n")
    for s in scenarios:
        click.echo(f"- {s.scenario_id}: {s.name} ({s.scenario_type.value})")
        click.echo(f"  {s.description}\n")

@scenario_cli.command(name="show")
@click.argument("scenario_id")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def show_scenario(scenario_id, json_output):
    """Show details of a specific scenario."""
    registry = create_scenario_registry(Settings())
    scenario = registry.get_scenario(scenario_id)

    if not scenario:
        click.secho(f"Error: Scenario '{scenario_id}' not found.", fg="red")
        raise click.Abort()

    if json_output:
        click.echo(json.dumps(scenario.model_dump(mode='json'), indent=2))
        return

    click.echo(f"Scenario: {scenario.name} ({scenario.scenario_id})")
    click.echo(f"Type: {scenario.scenario_type.value}")
    click.echo(f"Steps: {len(scenario.steps)}")
    for i, step in enumerate(scenario.steps, 1):
        click.echo(f"  {i}. {step.name} [{step.step_type.value}]")

@scenario_cli.command(name="run")
@click.argument("scenario_id")
@click.option("--compare-golden", is_flag=True, help="Compare results against golden snapshot.")
@click.option("--update-golden", is_flag=True, help="Update the golden snapshot.")
@click.option("--confirm", is_flag=True, help="Confirm updating the golden snapshot.")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def run_scenario(scenario_id, compare_golden, update_golden, confirm, json_output):
    """Run a specific scenario."""
    runner = create_scenario_runner(Settings())
    try:
        result = runner.run(
            scenario_id=scenario_id,
            compare_golden=compare_golden,
            update_golden=update_golden,
            confirm_update_golden=confirm
        )

        if json_output:
            click.echo(json.dumps(scenario_result_to_dict(result), indent=2))
            return

        from bist_signal_bot.scenarios.reporting import format_scenario_result_text
        click.echo(format_scenario_result_text(result))
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")
        raise click.Abort()

@scenario_cli.command(name="run-all")
@click.option("--type", "scenario_type", help="Run scenarios of specific type.")
@click.option("--stop-on-failure", is_flag=True, help="Stop on first failure.")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def run_all(scenario_type, stop_on_failure, json_output):
    """Run all scenarios or scenarios of a specific type."""
    from bist_signal_bot.scenarios.models import ScenarioType
    runner = create_scenario_runner(Settings())

    stype = ScenarioType(scenario_type) if scenario_type else None
    results = runner.run_all(scenario_type=stype, stop_on_failure=stop_on_failure)

    if json_output:
        click.echo(json.dumps([scenario_result_to_dict(r) for r in results], indent=2))
        return

    for r in results:
        click.echo(f"{r.scenario.scenario_id}: {r.status.value}")

@scenario_cli.command(name="replay")
@click.argument("run_id")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def replay_scenario(run_id, json_output):
    """Replay a specific past run by ID."""
    runner = create_scenario_runner(Settings())
    try:
        result = runner.replay(run_id)
        if json_output:
            click.echo(json.dumps(scenario_result_to_dict(result), indent=2))
            return
        from bist_signal_bot.scenarios.reporting import format_scenario_result_text
        click.echo(format_scenario_result_text(result))
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")

@scenario_cli.command(name="recent")
@click.option("--limit", type=int, default=10, help="Number of recent runs to show.")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def recent_runs(limit, json_output):
    """List recent scenario runs."""
    store = create_scenario_store(Settings())
    runs = store.list_recent_runs(limit=limit)
    if json_output:
        click.echo(json.dumps(runs, indent=2))
        return

    for r in runs:
        click.echo(f"{r['started_at']} - Run: {r['run_id']} - Scenario: {r['scenario_id']} - Status: {r['status']}")

@scenario_cli.group(name="golden")
def golden_cli():
    """Manage golden snapshots."""
    pass

@golden_cli.command(name="compare")
@click.argument("scenario_id")
def golden_compare(scenario_id):
    """Compare a scenario's last run against golden snapshot."""
    click.echo(f"Comparison requested for {scenario_id}.")

@golden_cli.command(name="update")
@click.argument("scenario_id")
@click.option("--confirm", is_flag=True, help="Confirm the update")
def golden_update(scenario_id, confirm):
    if not confirm:
        click.secho("Update requires --confirm flag.", fg="red")
        return
    click.echo(f"Golden update confirmed for {scenario_id}.")

@scenario_cli.command(name="cleanup")
@click.argument("run_id")
@click.option("--confirm", is_flag=True, help="Confirm cleanup")
def cleanup_scenario(run_id, confirm):
    """Clean up scenario sandbox."""
    runner = create_scenario_runner(Settings())
    try:
        res = runner.cleanup_sandbox(run_id, confirm=confirm)
        click.echo(f"Cleanup status: {res['status']}")
    except ValueError as e:
         click.secho(f"Error: {str(e)}", fg="red")

@scenario_cli.command(name="config")
@click.option("--json", "json_output", is_flag=True, help="Format output as JSON.")
def config_scenario(json_output):
    """Show current scenario runner configuration."""
    from bist_signal_bot.app.healthcheck_scenarios import check_scenarios
    cfg = check_scenarios(Settings())
    if json_output:
        click.echo(json.dumps(cfg, indent=2))
        return
    for k, v in cfg.items():
        click.echo(f"{k}: {v}")
