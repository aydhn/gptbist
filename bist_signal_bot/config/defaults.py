"""Native-typed default values for configuration keys that the code reads directly
but are **not** present in ``.env.example``.

Historically these keys resolved to the string ``"mock_value"`` (see the old
``Settings.__getattr__``), which silently broke every indicator, risk and
portfolio code path that expected an ``int`` window, a ``float`` ratio or a
``bool`` flag. This module supplies the real, conservative, research-only
defaults so the engines run correctly out of the box.

Resolution precedence in :mod:`bist_signal_bot.config.settings` is::

    os.environ  >  .env  >  .env.example  >  DEFAULTS (this file)  >  name-based guess

i.e. anything an operator sets in ``.env`` always wins; these values only fill
gaps. Standard technical-analysis window sizes are used where applicable.
"""
from __future__ import annotations

from typing import Any

DEFAULTS: dict[str, Any] = {
    # ---- Adaptive engine ----
    "ADAPTIVE_DEFAULT_TOP_N": 5,
    "ADAPTIVE_MODE": "ADVISORY",
    "ADAPTIVE_DIR_NAME": "adaptive",

    # ---- Momentum indicators (standard TA windows) ----
    "MOMENTUM_RSI_WINDOW": 14,
    "MOMENTUM_ROC_WINDOW": 12,
    "MOMENTUM_CCI_WINDOW": 20,
    "MOMENTUM_MFI_WINDOW": 14,
    "MOMENTUM_STOCH_K_WINDOW": 14,
    "MOMENTUM_STOCH_D_WINDOW": 3,
    "MOMENTUM_WILLIAMS_WINDOW": 14,

    # ---- Trend indicators ----
    "TREND_SHORT_WINDOW": 20,
    "TREND_MEDIUM_WINDOW": 50,
    "TREND_LONG_WINDOW": 200,
    "TREND_ADX_WINDOW": 14,
    "TREND_AROON_WINDOW": 25,
    "TREND_ATR_WINDOW": 14,
    "TREND_DONCHIAN_WINDOW": 20,
    "TREND_KELTNER_EMA_WINDOW": 20,
    "TREND_LINREG_WINDOW": 20,
    "TREND_SUPERTREND_ATR_WINDOW": 10,

    # ---- Volume indicators ----
    "VOLUME_WINDOW": 20,
    "VOLUME_CMF_WINDOW": 20,
    "VOLUME_EOM_WINDOW": 14,
    "VOLUME_LIQUIDITY_WINDOW": 20,
    "VOLUME_PRICE_WINDOW": 20,
    "VOLUME_MIN_TURNOVER_TRY": 1_000_000.0,

    # ---- Volatility indicators ----
    "VOL_WINDOW": 20,
    "VOL_ATR_WINDOW": 14,
    "VOL_BB_WINDOW": 20,
    "VOL_GAP_WINDOW": 20,
    "VOL_RANGE_WINDOW": 20,
    "VOL_RANK_WINDOW": 252,
    "VOL_REGIME_RANK_WINDOW": 252,
    "VOL_Z_WINDOW": 20,
    "VOL_ANNUALIZATION": 252.0,

    # ---- Candlestick / chart patterns ----
    "PATTERN_BREAKOUT_WINDOW": 20,
    "PATTERN_RANGE_WINDOW": 20,
    "PATTERN_SR_WINDOW": 20,
    "PATTERN_VOLUME_WINDOW": 20,
    "PATTERN_DOJI_BODY_THRESHOLD": 0.1,
    "PATTERN_GAP_THRESHOLD": 0.02,
    "PATTERN_SR_TOLERANCE_PCT": 0.02,
    "PATTERN_FEATURE_LEVEL": "STANDARD",

    # ---- Divergence detection ----
    "DIVERGENCE_MIN_PIVOT_DISTANCE": 5,
    "DIVERGENCE_MAX_PIVOT_DISTANCE": 60,
    "DIVERGENCE_MIN_STRENGTH_SCORE": 0.5,
    "DIVERGENCE_PIVOT_MODE": "FRACTAL",

    # ---- Risk engine (conservative, research defaults) ----
    "RISK_PER_TRADE_PCT": 0.01,
    "RISK_EQUITY_POSITION_PCT": 0.10,
    "RISK_FIXED_STOP_PCT": 0.05,
    "RISK_FIXED_TARGET_PCT": 0.10,
    "RISK_FIXED_NOTIONAL": 10_000.0,
    "RISK_MAX_ATR_PCT": 0.10,
    "RISK_MAX_COST_BPS": 50.0,
    "RISK_MAX_DAILY_SIGNALS": 20,
    "RISK_MAX_OPEN_POSITIONS": 10,
    "RISK_MAX_PORTFOLIO_RISK_PCT": 0.20,
    "RISK_MAX_POSITION_SIZE_PCT": 0.20,
    "RISK_MAX_VOLATILITY_PCT": 0.50,
    "RISK_MIN_AVG_TURNOVER_TRY": 1_000_000.0,
    "RISK_MIN_CONFIDENCE": 0.50,
    "RISK_MIN_RISK_REWARD": 1.5,
    "RISK_MIN_SIGNAL_SCORE": 0.50,
    "RISK_MIN_TRADE_NOTIONAL": 1_000.0,

    # ---- Portfolio construction ----
    "PORTFOLIO_DEFAULT_NOTIONAL": 100_000.0,
    "PORTFOLIO_MAX_CORRELATION_CLUSTER_WEIGHT": 0.40,
    "PORTFOLIO_MAX_COST_DRAG_BPS": 50.0,
    "PORTFOLIO_MAX_GROSS_EXPOSURE_PCT": 1.0,
    "PORTFOLIO_MAX_NET_EXPOSURE_PCT": 1.0,
    "PORTFOLIO_MAX_OPEN_POSITIONS": 10,
    "PORTFOLIO_MAX_POSITIONS": 10,
    "PORTFOLIO_MAX_SECTOR_WEIGHT": 0.30,
    "PORTFOLIO_MAX_SECTOR_WEIGHT_PCT": 0.30,
    "PORTFOLIO_MAX_SYMBOL_WEIGHT": 0.20,
    "PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT": 0.20,
    "PORTFOLIO_MIN_CASH_PCT": 0.05,
    "PORTFOLIO_REBALANCE_MIN_DELTA_WEIGHT": 0.01,
    "PORTFOLIO_TOTAL_ALLOCATION_PCT": 0.95,
    "PORTFOLIO_USE_CALIBRATED_CONFIDENCE": False,
    "PORTFOLIO_USE_MONTE_CARLO_SCORE": False,

    # ---- Backtest ----
    "BACKTEST_MAX_POSITION_SIZE_PCT": 0.20,
    "BACKTEST_MIN_TRADE_NOTIONAL": 1_000.0,
    "BACKTEST_PERIODS_PER_YEAR": 252,
    "BACKTEST_EXECUTION_PRICE_MODE": "CLOSE",

    # ---- Calibration ----
    "CALIBRATION_MIN_RECORDS": 30,
    "CALIBRATION_MIN_COHORT_SAMPLES": 10,
    "CALIBRATION_SUCCESS_RETURN_PCT": 0.05,
    "CALIBRATION_FAILURE_RETURN_PCT": -0.05,

    # ---- Data cleaning ----
    "CLEANING_MAX_DAILY_RETURN_ABS": 0.35,
    "CLEANING_MAX_VOLUME_ZSCORE": 10.0,
    "CLEANING_MIN_ROWS_AFTER_CLEANING": 100,

    # ---- Drift / Monte Carlo / Stress ----
    "DRIFT_MIN_SAMPLES": 30,
    "MONTE_CARLO_DRAWDOWN_THRESHOLD_PCT": 0.20,
    "STRESS_RUIN_THRESHOLD_PCT": 0.50,

    # ---- Leaderboard scoring ----
    "LEADERBOARD_MIN_CANDIDATES": 1,
    "LEADERBOARD_SCORE_PASS_THRESHOLD": 0.70,
    "LEADERBOARD_SCORE_WATCH_THRESHOLD": 0.50,
    "LEADERBOARD_SCORE_FAIL_THRESHOLD": 0.30,
    "LEADERBOARD_SELECTION_MIN_SAMPLE": 10,
    "LEADERBOARD_SELECTION_MIN_SCORE": 0.50,
    "LEADERBOARD_WEIGHT_CALIBRATION_SCORE": 0.33,
    "LEADERBOARD_WEIGHT_ROBUSTNESS_SCORE": 0.33,
    "LEADERBOARD_WEIGHT_VALIDATION_SCORE": 0.34,

    # ---- Knowledge memory ----
    "KNOWLEDGE_HYBRID_EMBEDDING_WEIGHT": 0.5,
    "KNOWLEDGE_HYBRID_KEYWORD_WEIGHT": 0.5,
    "KNOWLEDGE_MEMORY_MIN_CASES": 1,

    # ---- Runtime loop / jobs ----
    "RUNTIME_DEFAULT_TOP_N": 10,
    "RUNTIME_DEFAULT_STRATEGY": "moving_average_trend",
    "RUNTIME_JOB_MAX_RETRIES": 2,
    "RUNTIME_JOB_RETRY_DELAY_SECONDS": 5,
    "RUNTIME_JOB_TIMEOUT_SECONDS": 300,
    "RUNTIME_LOCK_TTL_SECONDS": 3600,
    "RUNTIME_MAX_ITERATIONS": 1,
    "RUNTIME_SLEEP_SECONDS": 60,
    "RUNTIME_UNIVERSE_MODE": "FILE",
    "RUNTIME_LOCK_FILE_NAME": "runtime.lock",
    "RUNTIME_STATE_FILE_NAME": "runtime_state.json",

    # ---- Telegram throttling ----
    "TELEGRAM_ERROR_COOLDOWN_SECONDS": 300,
    "TELEGRAM_RATE_LIMIT_SECONDS": 1,
    "TELEGRAM_SEND_TIMEOUT_SECONDS": 10,
    "TELEGRAM_CENTER_DIR_NAME": "telegram",

    # ---- Misc engine modes / strategies ----
    "DEFAULT_STRATEGY": "moving_average_trend",
    "DOWNLOAD_DEFAULT_PERIOD": "2y",
    "ENSEMBLE_WEIGHT_STRATEGY": "EQUAL",
    "MTF_ALIGNMENT_MODE": "STRICT",
    "PAPER_EXECUTION_MODE": "CLOSE",
    "PAPER_DEFAULT_ACCOUNT_ID": "default",
    "ERROR_NOTIFICATION_MIN_LEVEL": "ERROR",
    "DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB": 500,
    "QA_SYNTHETIC_PERIODS": 252,
    "PACKAGING_EXCLUDE_ENV_FILE": True,

    # ---- Directory names (storage layout) ----
    "BOOTSTRAP_DIR_NAME": "bootstrap",
    "DATA_IMPORT_DIR_NAME": "imports",
    "FINANCIALS_DIR_NAME": "financials",
    "LEADERBOARD_DIR_NAME": "leaderboard",
    "MACRO_DIR_NAME": "macro",
    "ML_MODELS_DIR_NAME": "ml_models",
    "ML_TRAINING_DIR_NAME": "ml_training",
    "OHLCV_DIR_NAME": "ohlcv",
    "OPS_DIR_NAME": "ops",
    "PAPER_ACCOUNTS_DIR_NAME": "paper_accounts",
    "UNIVERSE_DIR_NAME": "universe",
    "UNIVERSE_SNAPSHOTS_DIR_NAME": "universe_snapshots",
    "UNIVERSE_FILE_NAME": "universe.csv",
    "WATCHLISTS_DIR_NAME": "watchlists",
}
