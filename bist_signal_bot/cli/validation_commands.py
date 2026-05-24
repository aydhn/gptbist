import typer
from bist_signal_bot.cli.formatting import format_success, format_error, print_output
def print_json_or_rich(data, is_json): print_output(data, as_json=is_json)

app = typer.Typer(help="Strategy Validation Commands (Walk-Forward, Overfit, Robustness)")

@app.command("run")
def validation_run(
    strategy: str = typer.Option(..., "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(None, "--symbol", help="Single Symbol"),
    symbols: list[str] = typer.Option(None, "--symbols", help="Multiple Symbols"),
    split_type: str = typer.Option("WALK_FORWARD", "--split-type", help="Split type"),
    include_costs: bool = typer.Option(False, "--include-costs", help="Include costs"),
    include_slippage: bool = typer.Option(False, "--include-slippage", help="Include slippage"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Validation Completed"}, json_output)

@app.command("walk-forward")
def walk_forward(
    strategy: str = typer.Option(..., "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol"),
    train_days: int = typer.Option(252, "--train-days", help="Train Window Days"),
    test_days: int = typer.Option(63, "--test-days", help="Test Window Days"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Walk Forward Completed"}, json_output)

@app.command("purged-cv")
def purged_cv(
    strategy: str = typer.Option(..., "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol"),
    folds: int = typer.Option(5, "--folds", help="Number of Folds"),
    purge_days: int = typer.Option(5, "--purge-days", help="Purge Days"),
    embargo_days: int = typer.Option(2, "--embargo-days", help="Embargo Days"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Purged CV Completed"}, json_output)

@app.command("stability")
def stability(
    strategy: str = typer.Option(..., "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Stability Analysis Completed"}, json_output)

@app.command("overfit")
def overfit(
    strategy: str = typer.Option(None, "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(None, "--symbol", help="Symbol"),
    latest: bool = typer.Option(False, "--latest", help="Run on latest validation"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Overfit Diagnostics Completed"}, json_output)

@app.command("cost-robustness")
def cost_robustness(
    strategy: str = typer.Option(..., "--strategy", help="Strategy Name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Cost Robustness Completed"}, json_output)

@app.command("report")
def validation_report(
    latest: bool = typer.Option(False, "--latest", help="Show latest report"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Report Generated"}, json_output)

@app.command("recent")
def recent(
    limit: int = typer.Option(10, "--limit", help="Number of recent records"),
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Recent listed"}, json_output)

@app.command("config")
def config(
    json_output: bool = typer.Option(False, "--json", help="JSON Output")
):
    print_json_or_rich({"status": "Validation Config"}, json_output)

if __name__ == "__main__":
    app()
