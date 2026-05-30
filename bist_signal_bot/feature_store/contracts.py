from typing import Any
from bist_signal_bot.feature_store.models import FeatureContract, FeatureKind, FeatureDataType

class FeatureContractRegistry:
    def default_contracts(self) -> list[FeatureContract]:
        return [
            FeatureContract(contract_id="c_close_return_1d", feature_name="close_return_1d", feature_kind=FeatureKind.PRICE_ACTION, dtype=FeatureDataType.FLOAT, version="1.0", description="1-day return"),
            FeatureContract(contract_id="c_close_return_5d", feature_name="close_return_5d", feature_kind=FeatureKind.PRICE_ACTION, dtype=FeatureDataType.FLOAT, version="1.0", description="5-day return"),
            FeatureContract(contract_id="c_close_return_20d", feature_name="close_return_20d", feature_kind=FeatureKind.PRICE_ACTION, dtype=FeatureDataType.FLOAT, version="1.0", description="20-day return"),
            FeatureContract(contract_id="c_momentum_20d", feature_name="momentum_20d", feature_kind=FeatureKind.MOMENTUM, dtype=FeatureDataType.FLOAT, version="1.0", description="20-day momentum"),
            FeatureContract(contract_id="c_momentum_60d", feature_name="momentum_60d", feature_kind=FeatureKind.MOMENTUM, dtype=FeatureDataType.FLOAT, version="1.0", description="60-day momentum"),
            FeatureContract(contract_id="c_volatility_20d", feature_name="volatility_20d", feature_kind=FeatureKind.VOLATILITY, dtype=FeatureDataType.FLOAT, version="1.0", description="20-day volatility"),
            FeatureContract(contract_id="c_volatility_60d", feature_name="volatility_60d", feature_kind=FeatureKind.VOLATILITY, dtype=FeatureDataType.FLOAT, version="1.0", description="60-day volatility"),
            FeatureContract(contract_id="c_volume_zscore_20d", feature_name="volume_zscore_20d", feature_kind=FeatureKind.VOLUME, dtype=FeatureDataType.FLOAT, version="1.0", description="20-day volume z-score"),
            FeatureContract(contract_id="c_turnover_20d", feature_name="turnover_20d", feature_kind=FeatureKind.VOLUME, dtype=FeatureDataType.FLOAT, version="1.0", description="20-day turnover"),
            FeatureContract(contract_id="c_rsi_14", feature_name="rsi_14", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="RSI 14"),
            FeatureContract(contract_id="c_macd_signal", feature_name="macd_signal", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="MACD Signal"),
            FeatureContract(contract_id="c_moving_average_gap_20", feature_name="moving_average_gap_20", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="Moving Average Gap 20"),
            FeatureContract(contract_id="c_moving_average_gap_50", feature_name="moving_average_gap_50", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="Moving Average Gap 50"),
            FeatureContract(contract_id="c_atr_14", feature_name="atr_14", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="ATR 14"),
            FeatureContract(contract_id="c_liquidity_score", feature_name="liquidity_score", feature_kind=FeatureKind.LIQUIDITY, dtype=FeatureDataType.FLOAT, version="1.0", description="Liquidity Score"),
            FeatureContract(contract_id="c_valuation_score", feature_name="valuation_score", feature_kind=FeatureKind.VALUATION, dtype=FeatureDataType.FLOAT, version="1.0", description="Valuation Score"),
            FeatureContract(contract_id="c_earnings_quality_score", feature_name="earnings_quality_score", feature_kind=FeatureKind.FUNDAMENTAL, dtype=FeatureDataType.FLOAT, version="1.0", description="Earnings Quality Score"),
            FeatureContract(contract_id="c_factor_score", feature_name="factor_score", feature_kind=FeatureKind.FACTOR, dtype=FeatureDataType.FLOAT, version="1.0", description="Factor Score"),
            FeatureContract(contract_id="c_breadth_score", feature_name="breadth_score", feature_kind=FeatureKind.BREADTH, dtype=FeatureDataType.FLOAT, version="1.0", description="Breadth Score"),
            FeatureContract(contract_id="c_macro_pressure_score", feature_name="macro_pressure_score", feature_kind=FeatureKind.MACRO, dtype=FeatureDataType.FLOAT, version="1.0", description="Macro Pressure Score"),
            FeatureContract(contract_id="c_event_risk_score", feature_name="event_risk_score", feature_kind=FeatureKind.EVENT, dtype=FeatureDataType.FLOAT, version="1.0", description="Event Risk Score"),
            FeatureContract(contract_id="c_disclosure_risk_score", feature_name="disclosure_risk_score", feature_kind=FeatureKind.DISCLOSURE, dtype=FeatureDataType.FLOAT, version="1.0", description="Disclosure Risk Score")
        ]

    def get_contract(self, feature_name: str) -> FeatureContract | None:
        return next((c for c in self.default_contracts() if c.feature_name == feature_name), None)

    def validate_contract(self, contract: FeatureContract) -> list[str]:
        errors = []
        if not contract.version:
            errors.append("Contract version cannot be empty")
        if contract.allowed_null_ratio is not None and not (0 <= contract.allowed_null_ratio <= 1):
            errors.append("allowed_null_ratio must be between 0 and 1")
        if contract.lookback_days is not None and contract.lookback_days <= 0:
            errors.append("lookback_days must be positive")
        return errors

    def contracts_for_kind(self, kind: FeatureKind) -> list[FeatureContract]:
        return [c for c in self.default_contracts() if c.feature_kind == kind]

    def safe_contract_summary(self, contract: FeatureContract) -> dict[str, Any]:
        return {
            "feature_name": contract.feature_name,
            "kind": contract.feature_kind.value,
            "dtype": contract.dtype.value,
            "version": contract.version,
            "description": contract.description
        }
