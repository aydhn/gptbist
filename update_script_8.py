import os
import re

path = "bist_signal_bot/cli/commands.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    # Append ml-filter command group if not there
    if "@click.group(name=\"ml-filter\")" not in content:
        # First import ml-filter components
        imports = """
from bist_signal_bot.ml.inference.engine import MLInferenceEngine
from bist_signal_bot.ml.inference.models import MLInferenceInput
from bist_signal_bot.ml.inference.reporting import format_ml_inference_text, format_ml_signal_filter_text, format_ml_batch_text, ml_inference_batch_to_dataframe
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection"""

        content = content.replace("from bist_signal_bot.config.settings import Settings", "from bist_signal_bot.config.settings import Settings\n" + imports)

        ml_cmds = """
@click.group(name="ml-filter")
def ml_filter_group():
    \"\"\"ML Inference and Filtering commands.\"\"\"
    pass

@ml_filter_group.command(name="predict")
@click.argument("symbols", nargs=-1)
@click.option("--source", default="mock", help="Data source.")
@click.option("--model-id", required=True, help="Model ID.")
@click.option("--timeframe", default="1d", help="Timeframe.")
@click.option("--json", "output_json", is_flag=True, help="JSON output.")
@click.pass_obj
def ml_filter_predict(ctx, symbols, source, model_id, timeframe, output_json):
    if not symbols:
        click.echo("Provide at least one symbol.")
        return
    settings = ctx["settings"]
    data_svc = ctx["data_service"]
    engine = MLInferenceEngine.from_settings(settings)
    cfg = engine.build_default_config(model_id)
    cfg.enabled = True

    inputs = []
    for s in symbols:
        df = data_svc.get_data(s, source=source)
        inp = MLInferenceInput(symbol=s, data=df, config=cfg, timeframe=timeframe)
        inputs.append(inp)

    res = engine.predict_batch(inputs)

    if output_json:
        click.echo(ml_inference_batch_to_dataframe(res).to_json(orient="records"))
    else:
        click.echo(format_ml_batch_text(res))
        for r in res.results:
            click.echo("-" * 40)
            click.echo(format_ml_inference_text(r))

@ml_filter_group.command(name="signal")
@click.argument("symbol")
@click.option("--source", default="mock", help="Data source.")
@click.option("--strategy", required=True, help="Strategy name.")
@click.option("--model-id", required=True, help="Model ID.")
@click.option("--mode", help="MLInferenceMode (e.g. SCORE_ONLY).")
@click.option("--min-proba", type=float, help="Minimum probability positive.")
@click.option("--json", "output_json", is_flag=True, help="JSON output.")
@click.pass_obj
def ml_filter_signal(ctx, symbol, source, strategy, model_id, mode, min_proba, output_json):
    settings = ctx["settings"]
    data_svc = ctx["data_service"]
    strat_engine = ctx["strategy_engine"]
    engine = MLInferenceEngine.from_settings(settings)

    cfg = engine.build_default_config(model_id)
    cfg.enabled = True
    if mode:
        from bist_signal_bot.ml.inference.models import MLInferenceMode
        cfg.mode = MLInferenceMode(mode)
    if min_proba is not None:
        cfg.min_probability_positive = min_proba

    df = data_svc.get_data(symbol, source=source)
    from bist_signal_bot.strategies.models import StrategyRequest
    req = StrategyRequest(symbol=symbol, strategy_name=strategy, timeframe="1d")
    sig_batch = strat_engine.run(req, df)

    if not sig_batch.candidates:
        click.echo("No candidates produced by strategy.")
        return

    sig = sig_batch.candidates[0]
    res = engine.filter_signal(sig, symbol, df, cfg)

    if output_json:
        import json
        from bist_signal_bot.ml.inference.reporting import ml_signal_filter_result_to_dict
        click.echo(json.dumps(ml_signal_filter_result_to_dict(res), indent=2))
    else:
        click.echo(format_ml_signal_filter_text(res))

@ml_filter_group.command(name="batch")
@click.option("--symbols", required=True, help="Comma separated symbols.")
@click.option("--source", default="mock", help="Data source.")
@click.option("--strategy", required=True, help="Strategy name.")
@click.option("--model-id", required=True, help="Model ID.")
@click.option("--json", "output_json", is_flag=True, help="JSON output.")
@click.pass_obj
def ml_filter_batch(ctx, symbols, source, strategy, model_id, output_json):
    settings = ctx["settings"]
    data_svc = ctx["data_service"]
    strat_engine = ctx["strategy_engine"]
    engine = MLInferenceEngine.from_settings(settings)

    cfg = engine.build_default_config(model_id)
    cfg.enabled = True

    syms = [s.strip() for s in symbols.split(",")]

    inputs = []
    from bist_signal_bot.strategies.models import StrategyRequest
    for s in syms:
        df = data_svc.get_data(s, source=source)
        req = StrategyRequest(symbol=s, strategy_name=strategy, timeframe="1d")
        sig_batch = strat_engine.run(req, df)
        if sig_batch.candidates:
            inp = MLInferenceInput(symbol=s, data=df, signal=sig_batch.candidates[0], config=cfg)
            inputs.append(inp)

    res = engine.predict_batch(inputs)

    if output_json:
        click.echo(ml_inference_batch_to_dataframe(res).to_json(orient="records"))
    else:
        click.echo(format_ml_batch_text(res))

@ml_filter_group.command(name="config")
@click.option("--json", "output_json", is_flag=True, help="JSON output.")
@click.pass_obj
def ml_filter_config(ctx, output_json):
    settings = ctx["settings"]
    engine = MLInferenceEngine.from_settings(settings)
    cfg = engine.build_default_config()
    if output_json:
        import json
        click.echo(json.dumps(cfg.model_dump(), indent=2))
    else:
        click.echo("ML Filter Configuration:")
        for k, v in cfg.model_dump().items():
            if "model_" not in k and "secret" not in k:
                click.echo(f"  {k}: {v}")

cli.add_command(ml_filter_group)
"""
        content = content.replace("if __name__ == \"__main__\":", ml_cmds + "\nif __name__ == \"__main__\":")

        # Add flags to existing commands
        # strategies run
        strat_opts = """@click.option("--ml-filter", is_flag=True, help="Use ML Filter")
@click.option("--ml-model-id", help="ML Model ID")"""
        content = re.sub(r"@click\.option\(\"--benchmark\", help=\"Benchmark\"\)", "@click.option(\"--benchmark\", help=\"Benchmark\")\n" + strat_opts, content)
        content = re.sub(r"def strategies_run\(ctx, symbol, source, timeframe, strategy, benchmark\):", "def strategies_run(ctx, symbol, source, timeframe, strategy, benchmark, ml_filter, ml_model_id):", content)
        content = content.replace("req = StrategyRequest(", "req = StrategyRequest(\n        metadata={\"use_ml_filter\": ml_filter, \"ml_model_id\": ml_model_id},")

        # scan symbols
        scan_opts = """@click.option("--ml-filter", is_flag=True, help="Use ML Filter")
@click.option("--ml-model-id", help="ML Model ID")"""
        content = re.sub(r"@click\.option\(\"--sort\", default=\"FINAL_SCORE\", help=\"Sort key\"\)", "@click.option(\"--sort\", default=\"FINAL_SCORE\", help=\"Sort key\")\n" + scan_opts, content)
        content = re.sub(r"def scan_symbols\(ctx, symbols, source, timeframe, strategy, top_n, sort, descending\):", "def scan_symbols(ctx, symbols, source, timeframe, strategy, top_n, sort, descending, ml_filter, ml_model_id):", content)
        content = content.replace("req = ScanRequest(", "req = ScanRequest(\n        use_ml_filter=ml_filter,\n        ml_model_id=ml_model_id,")

        # backtest run
        content = re.sub(r"@click\.option\(\"--report\", \"save_report\", is_flag=True, help=\"Save report\"\)", "@click.option(\"--report\", \"save_report\", is_flag=True, help=\"Save report\")\n" + scan_opts, content)
        content = re.sub(r"def backtest_run\(ctx, symbol, source, timeframe, strategy, initial_capital, save_report\):", "def backtest_run(ctx, symbol, source, timeframe, strategy, initial_capital, save_report, ml_filter, ml_model_id):", content)
        content = content.replace("config = BacktestConfig(", "config = BacktestConfig(\n        use_ml_filter=ml_filter,\n        ml_model_id=ml_model_id,")

        # paper run-once
        content = re.sub(r"@click\.option\(\"--short\", \"allow_short\", is_flag=True, help=\"Allow short\"\)", "@click.option(\"--short\", \"allow_short\", is_flag=True, help=\"Allow short\")\n" + scan_opts, content)
        content = re.sub(r"def paper_run_once\(ctx, symbol, source, account, strategy, short\):", "def paper_run_once(ctx, symbol, source, account, strategy, short, ml_filter, ml_model_id):", content)
        content = content.replace("req = PaperRunRequest(", "req = PaperRunRequest(\n        use_ml_filter=ml_filter,\n        ml_model_id=ml_model_id,")

        with open(path, "w") as f:
            f.write(content)

print("Updated CLI commands")
