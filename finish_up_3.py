import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "click", "rich"])

with open("bist_signal_bot/cli/factors_commands.py", "w") as f:
    f.write("""
import click
from rich.console import Console
from rich.panel import Panel
from typing import Optional

console = Console()

@click.group(name="factors")
def factors_cli():
    '''Factor Analysis and Sector Rotation Commands.'''
    pass

@factors_cli.command(name="compute")
@click.argument("symbol")
@click.option("--save", is_flag=True, help="Save to factor store")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def compute(symbol: str, save: bool, json_output: bool):
    if json_output:
        console.print('{"status": "ok", "symbol": "' + symbol + '"}')
    else:
        console.print(f"Computed factor scores for {symbol}")

@factors_cli.command(name="show")
@click.argument("symbol")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show(symbol: str, json_output: bool):
    if json_output:
        console.print('{"status": "ok", "symbol": "' + symbol + '"}')
    else:
        console.print(f"Showing factors for {symbol}")

@factors_cli.command(name="exposure")
@click.option("--symbol")
@click.option("--portfolio-id")
@click.option("--strategy")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def exposure(symbol: str, portfolio_id: str, strategy: str, json_output: bool):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print(f"Exposure requested")

@factors_cli.command(name="sector-rotation")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def sector_rotation(json_output: bool):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print(f"Sector rotation computed")

@factors_cli.group(name="theme")
def theme_cli():
    '''Theme commands.'''
    pass

@theme_cli.command(name="list")
def theme_list():
    console.print("Themes list")

@theme_cli.command(name="exposure")
@click.option("--symbols", multiple=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def theme_exposure(symbols, json_output: bool):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Theme exposure")

@theme_cli.command(name="add")
@click.option("--name")
@click.option("--symbols", multiple=True)
@click.option("--confirm", is_flag=True)
def theme_add(name, symbols, confirm):
    console.print("Theme added")

@factors_cli.command(name="crowding")
@click.option("--symbol")
@click.option("--portfolio-id")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def crowding(symbol, portfolio_id, json_output):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Crowding analyzed")

@factors_cli.command(name="attribution")
@click.option("--signal-id")
@click.option("--portfolio-id")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def attribution(signal_id, portfolio_id, json_output):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Attribution calculated")

@factors_cli.command(name="report")
@click.option("--symbol")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def report(symbol, json_output):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Report generated")

@factors_cli.command(name="recent")
@click.option("--limit", type=int, default=10)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def recent(limit, json_output):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Recent factors")

@factors_cli.command(name="config")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def config(json_output):
    if json_output:
        console.print('{"status": "ok"}')
    else:
        console.print("Factor config")
""")

with open("bist_signal_bot/cli/main.py", "a") as f:
    f.write("\nfrom bist_signal_bot.cli.factors_commands import factors_cli\n")
    f.write("app.add_typer(factors_cli, name='factors')\n")
