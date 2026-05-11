import os
import re

path = "bist_signal_bot/backtesting/engine.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "from bist_signal_bot.ml.inference.engine import MLInferenceEngine" not in content:
        content = content.replace("from bist_signal_bot.backtesting.models import (",
                                  "from bist_signal_bot.ml.inference.engine import MLInferenceEngine\nfrom bist_signal_bot.ml.inference.models import MLInferenceConfig, MLFilterDecision\nfrom bist_signal_bot.backtesting.models import (")

        # update constructor
        content = re.sub(
            r"def __init__\(self,\n\s*data_service: MarketDataService,\n\s*strategy_engine: StrategyEngine,\n\s*risk_engine: RiskEngine \| None = None,\n\s*settings: Settings \| None = None,\n\s*logger: logging\.Logger \| None = None\):",
            "def __init__(self,\n                 data_service: MarketDataService,\n                 strategy_engine: StrategyEngine,\n                 risk_engine: RiskEngine | None = None,\n                 ml_inference_engine: MLInferenceEngine | None = None,\n                 settings: Settings | None = None,\n                 logger: logging.Logger | None = None):",
            content
        )
        content = content.replace("self.risk_engine = risk_engine", "self.risk_engine = risk_engine\n        self.ml_inference_engine = ml_inference_engine")

        # update process bar
        process_bar_str = """
            if signal:
                if signal.is_actionable_candidate():
                    # Apply ML filter recursively capping data up to i+1
                    if config.use_ml_filter and self.ml_inference_engine:
                        ml_id = config.ml_model_id or getattr(self.settings, "BACKTEST_ML_MODEL_ID", None)
                        if ml_id:
                            ml_cfg = self.ml_inference_engine.build_default_config(ml_id)
                            ml_cfg.enabled = True

                            # Capped data strictly up to current bar to prevent leakage
                            capped_data = data.iloc[:i+1].copy()

                            filter_res = self.ml_inference_engine.filter_signal(signal, config.symbol, capped_data, ml_cfg, timeframe=config.timeframe)
                            signal = filter_res.adjusted_signal
                            if filter_res.inference_result.filter_decision == MLFilterDecision.REJECT:
                                continue # skip creating order

                    self._create_order_from_signal(signal, config, current_ts)"""

        content = re.sub(
            r"if signal:\n\s*if signal\.is_actionable_candidate\(\):\n\s*self\._create_order_from_signal\(signal, config, current_ts\)",
            process_bar_str,
            content
        )
        with open(path, "w") as f:
            f.write(content)

print("Updated backtesting engine")
