from typing import Any

from bist_signal_bot.core.exceptions import CommissionModelError
from bist_signal_bot.costs.models import (
    CommissionModelType,
    CommissionResult,
    TradeCostInput,
)


class CommissionModel:
    def __init__(
        self,
        model_type: CommissionModelType = CommissionModelType.BPS,
        commission_bps: float = 5.0,
        flat_fee: float = 0.0,
        minimum_commission: float = 0.0,
        tax_bps: float = 0.0,
        other_fee_bps: float = 0.0,
    ):
        if commission_bps < 0:
            raise CommissionModelError("commission_bps cannot be negative")
        if flat_fee < 0:
            raise CommissionModelError("flat_fee cannot be negative")
        if minimum_commission < 0:
            raise CommissionModelError("minimum_commission cannot be negative")
        if tax_bps < 0:
            raise CommissionModelError("tax_bps cannot be negative")
        if other_fee_bps < 0:
            raise CommissionModelError("other_fee_bps cannot be negative")

        self.model_type = model_type
        self.commission_bps = commission_bps
        self.flat_fee = flat_fee
        self.minimum_commission = minimum_commission
        self.tax_bps = tax_bps
        self.other_fee_bps = other_fee_bps

    def calculate(self, input_data: TradeCostInput) -> CommissionResult:
        notional = input_data.computed_notional()

        commission_amount = 0.0

        if self.model_type == CommissionModelType.BPS:
            commission_amount = notional * (self.commission_bps / 10000.0)
        elif self.model_type == CommissionModelType.FLAT:
            commission_amount = self.flat_fee
        elif self.model_type == CommissionModelType.BPS_PLUS_FLAT:
            commission_amount = (notional * (self.commission_bps / 10000.0)) + self.flat_fee
        else:
            raise CommissionModelError(f"Unsupported commission model type: {self.model_type}")

        min_commission_applied = False
        if commission_amount < self.minimum_commission:
            commission_amount = self.minimum_commission
            min_commission_applied = True

        return CommissionResult(
            commission_amount=commission_amount,
            commission_rate_bps=self.commission_bps,
            flat_fee=self.flat_fee,
            min_commission_applied=min_commission_applied,
            metadata={
                "model_type": self.model_type.value
            }
        )

    def calculate_tax(self, input_data: TradeCostInput) -> float:
        notional = input_data.computed_notional()
        return notional * (self.tax_bps / 10000.0)

    def calculate_other_fees(self, input_data: TradeCostInput) -> float:
        notional = input_data.computed_notional()
        return notional * (self.other_fee_bps / 10000.0)
