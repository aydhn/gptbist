import os
import re

# Update paper engine
path = "bist_signal_bot/paper/engine.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "ml_inference_engine" not in content:
        content = content.replace("from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine",
                                  "from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine\nfrom bist_signal_bot.ml.inference.engine import MLInferenceEngine\nfrom bist_signal_bot.ml.inference.models import MLInferenceConfig, MLFilterDecision")

        # In RunOnce request, we need to add fields but we might not have a model for it since it uses a dict/kwargs or PaperRunRequest
        req_repl = """
    timeframe: str = "1d"
    use_ml_filter: bool = False
    ml_model_id: str | None = None"""
        content = content.replace("timeframe: str = \"1d\"", req_repl)

        # update init
        content = re.sub(
            r"def __init__\(self,\n\s*ledger: PaperLedger,\n\s*market_data: MarketDataService \| None = None,\n\s*strategy_engine: StrategyEngine \| None = None,\n\s*risk_engine: RiskEngine \| None = None,\n\s*portfolio_risk_engine: PortfolioRiskEngine \| None = None,\n\s*settings: Settings \| None = None\):",
            "def __init__(self,\n                 ledger: PaperLedger,\n                 market_data: MarketDataService | None = None,\n                 strategy_engine: StrategyEngine | None = None,\n                 risk_engine: RiskEngine | None = None,\n                 portfolio_risk_engine: PortfolioRiskEngine | None = None,\n                 ml_inference_engine: MLInferenceEngine | None = None,\n                 settings: Settings | None = None):",
            content
        )
        content = content.replace("self.portfolio_risk = portfolio_risk_engine", "self.portfolio_risk = portfolio_risk_engine\n        self.ml_inference_engine = ml_inference_engine")

        run_once_repl = """
            if not signal.is_actionable_candidate():
                continue

            if request.use_ml_filter and self.ml_inference_engine:
                ml_id = request.ml_model_id or getattr(self.settings, "PAPER_ML_MODEL_ID", None)
                if ml_id:
                    ml_cfg = self.ml_inference_engine.build_default_config(ml_id)
                    ml_cfg.enabled = True
                    filter_res = self.ml_inference_engine.filter_signal(signal, sym, df, ml_cfg, timeframe=request.timeframe)
                    signal = filter_res.adjusted_signal
                    if filter_res.inference_result.filter_decision == MLFilterDecision.REJECT:
                        self.logger.info(f"[{sym}] ML filter rejected paper simulation candidate.")
                        res["failed_count"] += 1
                        res["issues"].append(f"{sym}: ML Filter rejected")
                        continue"""

        content = re.sub(
            r"if not signal\.is_actionable_candidate\(\):\n\s*continue",
            run_once_repl,
            content
        )
        with open(path, "w") as f:
            f.write(content)

print("Updated paper engine")
