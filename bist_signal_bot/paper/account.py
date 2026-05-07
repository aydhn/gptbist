from datetime import datetime, UTC
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperAccountError
from bist_signal_bot.paper.models import (
    PaperAccount,
    PaperAccountStatus,
    PaperPosition
)


class PaperAccountManager:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def create_account(self, initial_cash: Optional[float] = None, account_id: Optional[str] = None) -> PaperAccount:
        acc_id = account_id or self.settings.PAPER_DEFAULT_ACCOUNT_ID
        cash = initial_cash if initial_cash is not None else self.settings.PAPER_INITIAL_CASH

        if cash <= 0:
            raise PaperAccountError("initial_cash must be positive", context={"account_id": acc_id, "initial_cash": cash})

        return PaperAccount(
            account_id=acc_id,
            status=PaperAccountStatus.ACTIVE,
            initial_cash=cash,
            cash=cash,
            equity=cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            total_costs=0.0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def reset_account(self, account: PaperAccount, initial_cash: Optional[float] = None) -> PaperAccount:
        cash = initial_cash if initial_cash is not None else self.settings.PAPER_INITIAL_CASH

        if cash <= 0:
            raise PaperAccountError("initial_cash must be positive", context={"account_id": account.account_id, "initial_cash": cash})

        account.status = PaperAccountStatus.ACTIVE
        account.initial_cash = cash
        account.cash = cash
        account.equity = cash
        account.realized_pnl = 0.0
        account.unrealized_pnl = 0.0
        account.total_costs = 0.0
        account.updated_at = datetime.now(UTC)
        return account

    def pause_account(self, account: PaperAccount) -> PaperAccount:
        account.status = PaperAccountStatus.PAUSED
        account.updated_at = datetime.now(UTC)
        return account

    def activate_account(self, account: PaperAccount) -> PaperAccount:
        account.status = PaperAccountStatus.ACTIVE
        account.updated_at = datetime.now(UTC)
        return account

    def update_equity(self, account: PaperAccount, positions: list[PaperPosition]) -> PaperAccount:
        unrealized_pnl = sum(p.unrealized_pnl for p in positions if p.is_open)
        market_value = sum(p.market_value for p in positions if p.is_open)

        account.unrealized_pnl = unrealized_pnl
        account.equity = account.cash + market_value
        account.updated_at = datetime.now(UTC)
        return account

    def apply_cash_change(self, account: PaperAccount, amount: float, reason: str) -> PaperAccount:
        new_cash = account.cash + amount
        if new_cash < 0:
            raise PaperAccountError(f"Insufficient cash for operation ({reason})",
                                    context={"current_cash": account.cash, "amount": amount})

        account.cash = new_cash
        account.updated_at = datetime.now(UTC)
        return account
