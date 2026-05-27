import uuid
from datetime import datetime, timezone
from typing import Any, Optional, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import (
    ValuationMetricType, ValuationStatus, ValuationMarketInput, ValuationMultiple
)

class ValuationMultipleCalculator:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.epsilon = getattr(self.settings, "VALUATION_DENOMINATOR_EPSILON", 1e-9)
        self.extreme_warn = getattr(self.settings, "VALUATION_EXTREME_MULTIPLE_ABS_WARN", 1000.0)

    def safe_divide(self, numerator: Optional[float], denominator: Optional[float], metric_name: str) -> tuple[Optional[float], list[str]]:
        warnings = []
        if numerator is None or denominator is None:
            return None, warnings
        if abs(denominator) < self.epsilon:
            warnings.append(f"Denominator for {metric_name} is practically zero.")
            return None, warnings

        value = numerator / denominator
        if abs(value) > self.extreme_warn:
            warnings.append(f"Data quality warning: {metric_name} value ({value:.2f}) is extremely high/low.")

        return value, warnings

    def _build_multiple(self, symbol: str, metric_type: ValuationMetricType, as_of: datetime,
                        numerator: Optional[float], denominator: Optional[float],
                        value: Optional[float], warnings: List[str], statement: Any = None) -> ValuationMultiple:

        status = ValuationStatus.UNKNOWN
        if value is not None:
            status = ValuationStatus.FAIR # Placeholder, scored later
        elif numerator is None or denominator is None:
            status = ValuationStatus.INSUFFICIENT_DATA

        fiscal_year = getattr(statement, "fiscal_year", None) if statement else None
        fiscal_period = getattr(statement, "fiscal_period", None) if statement else None

        return ValuationMultiple(
            multiple_id=str(uuid.uuid4()),
            symbol=symbol,
            metric_type=metric_type,
            as_of=as_of,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            numerator=numerator,
            denominator=denominator,
            value=value,
            status=status,
            warnings=warnings
        )

    def calculate_all(self, symbol: str, market_input: ValuationMarketInput, statement: Any = None, dividend_payload: Optional[dict] = None) -> List[ValuationMultiple]:
        results = []
        if getattr(self.settings, "VALUATION_CALCULATE_PE", True):
            results.append(self.calculate_pe(market_input, statement))
        if getattr(self.settings, "VALUATION_CALCULATE_PB", True):
            results.append(self.calculate_pb(market_input, statement))
        if getattr(self.settings, "VALUATION_CALCULATE_EV_EBITDA", True):
            results.append(self.calculate_ev_ebitda(market_input, statement))
        if getattr(self.settings, "VALUATION_CALCULATE_EV_SALES", True):
            results.append(self.calculate_ev_sales(market_input, statement))

        results.append(self.calculate_price_sales(market_input, statement))

        if getattr(self.settings, "VALUATION_CALCULATE_FCF_YIELD", True):
            results.append(self.calculate_fcf_yield(market_input, statement))

        results.append(self.calculate_earnings_yield(market_input, statement))

        if dividend_payload:
            results.append(self.calculate_dividend_yield(market_input, dividend_payload))

        return results

    def calculate_pe(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        net_income = getattr(statement, "net_income", None) if statement else None
        value, warnings = self.safe_divide(input.market_cap, net_income, "PE")

        if net_income is not None and net_income < 0:
            warnings.append("Negative earnings; PE evaluated as WATCH.")

        multiple = self._build_multiple(input.symbol, ValuationMetricType.PE, input.as_of, input.market_cap, net_income, value, warnings, statement)
        if net_income is not None and net_income < 0:
            multiple.status = ValuationStatus.WATCH
        return multiple

    def calculate_pb(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        equity = getattr(statement, "total_equity", None) if statement else None
        value, warnings = self.safe_divide(input.market_cap, equity, "PB")

        if equity is not None and equity < 0:
            warnings.append("Negative equity; PB evaluated as WATCH.")

        multiple = self._build_multiple(input.symbol, ValuationMetricType.PB, input.as_of, input.market_cap, equity, value, warnings, statement)
        if equity is not None and equity < 0:
            multiple.status = ValuationStatus.WATCH
        return multiple

    def calculate_ev_ebitda(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        ebitda = getattr(statement, "ebitda", None) if statement else None
        value, warnings = self.safe_divide(input.enterprise_value, ebitda, "EV_EBITDA")

        if ebitda is not None and ebitda < 0:
            warnings.append("Negative EBITDA; EV/EBITDA evaluated as WATCH.")

        multiple = self._build_multiple(input.symbol, ValuationMetricType.EV_EBITDA, input.as_of, input.enterprise_value, ebitda, value, warnings, statement)
        if ebitda is not None and ebitda < 0:
            multiple.status = ValuationStatus.WATCH
        return multiple

    def calculate_ev_sales(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        revenue = getattr(statement, "revenue", None) if statement else None
        value, warnings = self.safe_divide(input.enterprise_value, revenue, "EV_SALES")
        return self._build_multiple(input.symbol, ValuationMetricType.EV_SALES, input.as_of, input.enterprise_value, revenue, value, warnings, statement)

    def calculate_price_sales(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        revenue = getattr(statement, "revenue", None) if statement else None
        value, warnings = self.safe_divide(input.market_cap, revenue, "PRICE_SALES")
        return self._build_multiple(input.symbol, ValuationMetricType.PRICE_SALES, input.as_of, input.market_cap, revenue, value, warnings, statement)

    def calculate_fcf_yield(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        fcf = getattr(statement, "free_cash_flow", None) if statement else None
        value, warnings = self.safe_divide(fcf, input.market_cap, "FCF_YIELD")
        return self._build_multiple(input.symbol, ValuationMetricType.FCF_YIELD, input.as_of, fcf, input.market_cap, value, warnings, statement)

    def calculate_earnings_yield(self, input: ValuationMarketInput, statement: Any) -> ValuationMultiple:
        net_income = getattr(statement, "net_income", None) if statement else None
        value, warnings = self.safe_divide(net_income, input.market_cap, "EARNINGS_YIELD")
        return self._build_multiple(input.symbol, ValuationMetricType.EARNINGS_YIELD, input.as_of, net_income, input.market_cap, value, warnings, statement)

    def calculate_dividend_yield(self, input: ValuationMarketInput, dividend_payload: dict) -> ValuationMultiple:
        dividend = dividend_payload.get("annual_dividend")
        value, warnings = self.safe_divide(dividend, input.price, "DIVIDEND_YIELD")
        return self._build_multiple(input.symbol, ValuationMetricType.DIVIDEND_YIELD, input.as_of, dividend, input.price, value, warnings)
