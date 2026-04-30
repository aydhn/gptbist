import logging
import time
from typing import List, Dict, Any, Tuple, Union
import pandas as pd
from datetime import datetime

from bist_signal_bot.indicators.models import (
    IndicatorRequest, IndicatorResult, IndicatorBatchResult, IndicatorIssue
)
from bist_signal_bot.indicators.registry import IndicatorRegistry
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import IndicatorCalculationError, IndicatorValidationError, IndicatorRegistryError
from bist_signal_bot.data.models import MarketDataFrame

class IndicatorEngine:
    def __init__(self, registry: IndicatorRegistry | None = None, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.registry = registry or IndicatorRegistry.create_default_registry()
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def calculate(self, data: Union[MarketDataFrame, pd.DataFrame], request: IndicatorRequest) -> Tuple[pd.DataFrame, IndicatorResult]:
        start_time = time.time()

        # Extract dataframe if MarketDataFrame is provided
        df = data.data.copy() if isinstance(data, MarketDataFrame) else data.copy()

        issues = []
        status = "SUCCESS"
        output_cols = []

        try:
            indicator = self.registry.get(request.name)

            # Warn if not enough rows
            if len(df) < indicator.spec.min_rows:
                issues.append(IndicatorIssue(
                    indicator=request.name,
                    message=f"Not enough rows for {request.name}. Provided: {len(df)}, Required min: {indicator.spec.min_rows}",
                    severity="WARNING",
                    metadata={"provided_rows": len(df), "min_rows": indicator.spec.min_rows}
                ))

            result_df = indicator(df, **request.params)

            # Rename columns if a prefix is requested
            if request.output_prefix:
                rename_map = {col: f"{request.output_prefix}{col}" for col in result_df.columns}
                result_df = result_df.rename(columns=rename_map)

            output_cols = list(result_df.columns)

            # Check for high NaN count
            nan_count = result_df.isna().sum().sum()

            # Combine into input
            df = pd.concat([df, result_df], axis=1)

        except (IndicatorValidationError, IndicatorCalculationError, IndicatorRegistryError) as e:
            status = "FAILED"
            issues.append(IndicatorIssue(
                indicator=request.name,
                message=str(e),
                severity="ERROR"
            ))
            nan_count = 0

            if not getattr(self.settings, 'INDICATOR_CONTINUE_ON_ERROR', True):
                raise e

        elapsed = time.time() - start_time

        result = IndicatorResult(
            indicator=request.name,
            status=status,
            output_columns=output_cols,
            row_count=len(df),
            nan_count=int(nan_count),
            issues=issues,
            elapsed_seconds=elapsed
        )

        return df, result

    def calculate_many(self, data: Union[MarketDataFrame, pd.DataFrame], requests: List[IndicatorRequest], continue_on_error: bool = True) -> IndicatorBatchResult:
        start_time = time.time()

        df = data.data.copy() if isinstance(data, MarketDataFrame) else data.copy()

        results = []
        success_count = 0
        failed_count = 0

        for request in requests:
            try:
                df, result = self.calculate(df, request)
                results.append(result)
                if result.status == "SUCCESS":
                    success_count += 1
                else:
                    failed_count += 1
                    if not continue_on_error:
                        # We just let it raise a generic error or original if available in calculate.
                        # Wait, we must explicitly raise the exception here if we want to fail fast
                        raise IndicatorCalculationError(f"Calculation failed for {request.name}")
            except Exception as e:
                if not continue_on_error:
                    raise
                # Create a failed result if an unhandled exception occurred
                failed_count += 1
                results.append(IndicatorResult(
                    indicator=request.name,
                    status="FAILED",
                    output_columns=[],
                    row_count=len(df),
                    nan_count=0,
                    issues=[IndicatorIssue(indicator=request.name, message=str(e), severity="ERROR")],
                    elapsed_seconds=0.0
                ))

        elapsed = time.time() - start_time

        return IndicatorBatchResult(
            results=results,
            output_data=df,
            requested_count=len(requests),
            success_count=success_count,
            failed_count=failed_count,
            elapsed_seconds=elapsed
        )

    def calculate_default_set(self, data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        default_set_str = getattr(self.settings, 'INDICATOR_DEFAULT_SET', "sma_20,sma_50,ema_20,rsi_14,atr_14,macd,bb_20,obv,return_1,volatility_20")
        requests_raw = default_set_str.split(",")
        requests = self.parse_requests(requests_raw)
        return self.calculate_many(data, requests)

    def parse_requests(self, raw: List[str]) -> List[IndicatorRequest]:
        requests = []
        for item in raw:
            item = item.strip()
            if not item:
                continue

            parts = item.split(":")
            name = parts[0]
            params = {}

            # Simple heuristic for common defaults if parameters aren't specified via ":"
            if "_" in name and not ":" in item:
                # Attempt to parse names like sma_20, macd_12_26_9
                subparts = name.split("_")
                base_name = subparts[0]

                # We can't automatically parse all generic types without registry knowledge,
                # but we can do a best effort or just fall back to requiring proper syntax.
                # Here we handle simple known ones or rely on proper parsing
                if len(subparts) == 2 and subparts[1].isdigit():
                    name = base_name
                    # Assuming window/span based on common patterns
                    if base_name in ["sma", "wma", "rsi", "roc", "atr", "volatility"]:
                        params["window"] = int(subparts[1])
                    elif base_name in ["ema"]:
                        params["span"] = int(subparts[1])
                    elif base_name in ["return", "log_return"]:
                        params["periods"] = int(subparts[1])

            if len(parts) > 1:
                param_str = parts[1]
                param_pairs = param_str.split(",")
                for pair in param_pairs:
                    if "=" in pair:
                        k, v = pair.split("=")
                        k, v = k.strip(), v.strip()
                        # Try to cast
                        if v.isdigit():
                            v = int(v)
                        elif v.replace('.', '', 1).isdigit() and v.count('.') == 1:
                            v = float(v)
                        elif v.lower() == 'true':
                            v = True
                        elif v.lower() == 'false':
                            v = False
                        params[k] = v

            requests.append(IndicatorRequest(name=name, params=params))

        return requests
