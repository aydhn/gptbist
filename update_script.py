import os
import re

# Update strategies/engine.py
path = "bist_signal_bot/strategies/engine.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "from bist_signal_bot.ml.inference.engine import MLInferenceEngine" not in content:
        content = content.replace("from bist_signal_bot.strategies.registry import StrategyRegistry",
                                  "from bist_signal_bot.strategies.registry import StrategyRegistry\nfrom bist_signal_bot.ml.inference.engine import MLInferenceEngine\nfrom bist_signal_bot.ml.inference.models import MLInferenceConfig, MLInferenceMode\nfrom bist_signal_bot.ml.inference.models import MLFilterDecision")

        content = re.sub(
            r"def __init__\(self,\n\s*registry: StrategyRegistry,",
            "def __init__(self,\n                 registry: StrategyRegistry,\n                 ml_inference_engine: MLInferenceEngine | None = None,",
            content
        )
        content = content.replace("self.registry = registry", "self.registry = registry\n        self.ml_inference_engine = ml_inference_engine")

        # update run method inside strategies/engine.py to include ML logic
        run_repl = """
            if signal:
                # ML filter integration
                use_ml = request.metadata.get("use_ml_filter", False)
                ml_model_id = request.metadata.get("ml_model_id", None)

                if use_ml and self.ml_inference_engine:
                    cfg = self.ml_inference_engine.build_default_config(ml_model_id)
                    cfg.enabled = True
                    filter_res = self.ml_inference_engine.filter_signal(signal, symbol, data, cfg, timeframe=request.timeframe)

                    if filter_res.passed:
                        signal = filter_res.adjusted_signal
                    else:
                        # Convert to AVOID/WATCH based on decision
                        if filter_res.inference_result.filter_decision == MLFilterDecision.REJECT:
                            signal.direction = SignalDirection.AVOID
                            signal.status = SignalStatus.REJECTED
                        elif filter_res.inference_result.filter_decision == MLFilterDecision.WATCH_ONLY:
                            signal.direction = SignalDirection.WATCH

                        # Apply adjusted metadata anyways
                        signal = filter_res.adjusted_signal

                results.append(signal)"""

        content = re.sub(r"if signal:\n\s*results\.append\(signal\)", run_repl, content)

        with open(path, "w") as f:
            f.write(content)

# Update scanner/engine.py
path = "bist_signal_bot/scanner/engine.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "ml_inference_engine" not in content:
        content = content.replace("from bist_signal_bot.strategies.engine import StrategyEngine",
                                  "from bist_signal_bot.strategies.engine import StrategyEngine\nfrom bist_signal_bot.ml.inference.engine import MLInferenceEngine\nfrom bist_signal_bot.ml.inference.models import MLInferenceConfig, MLFilterDecision")

        content = re.sub(
            r"def __init__\(self,\n\s*strategy_engine: StrategyEngine,",
            "def __init__(self,\n                 strategy_engine: StrategyEngine,\n                 ml_inference_engine: MLInferenceEngine | None = None,",
            content
        )
        content = content.replace("self.strategy_engine = strategy_engine", "self.strategy_engine = strategy_engine\n        self.ml_inference_engine = ml_inference_engine")

        scan_sym_repl = """
            # ML Filter Injection
            use_ml = request.use_ml_filter if hasattr(request, "use_ml_filter") else self.settings.SCANNER_USE_ML_FILTER
            if use_ml and self.ml_inference_engine and signal:
                ml_id = request.ml_model_id if hasattr(request, "ml_model_id") else self.settings.SCANNER_ML_MODEL_ID
                cfg = self.ml_inference_engine.build_default_config(ml_id)
                cfg.enabled = True

                # Check min prob overrides
                if hasattr(request, "min_ml_probability") and request.min_ml_probability is not None:
                    cfg.min_probability_positive = request.min_ml_probability
                if hasattr(request, "min_ml_score") and request.min_ml_score is not None:
                    cfg.min_prediction_score = request.min_ml_score

                filter_res = self.ml_inference_engine.filter_signal(signal, symbol, df, cfg, timeframe=request.timeframe)
                signal = filter_res.adjusted_signal

                if not filter_res.passed:
                    res.status = SymbolScanStatus.REJECTED
                    res.reject_reason = filter_res.reject_reason or "Rejected by ML Filter"
                    res.reasons.append(res.reject_reason)

            res.signal = signal"""

        content = content.replace("res.signal = signal", scan_sym_repl)
        with open(path, "w") as f:
            f.write(content)

print("Updated engines")
