import pytest
from bist_signal_bot.paper.account import PaperAccountManager
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.paper.models import PaperAccountStatus

def test_paper_account_manager_create():
    # 6. PaperAccountManager create_account çalışır.
    manager = PaperAccountManager(Settings())
    acc = manager.create_account(initial_cash=5000, account_id="my_acc")
    assert acc.account_id == "my_acc"
    assert acc.initial_cash == 5000
    assert acc.cash == 5000

def test_paper_account_manager_reset():
    # 7. PaperAccountManager reset_account çalışır.
    manager = PaperAccountManager(Settings())
    acc = manager.create_account(initial_cash=5000, account_id="my_acc")
    acc.cash = 100

    acc = manager.reset_account(acc, initial_cash=10000)
    assert acc.initial_cash == 10000
    assert acc.cash == 10000
    assert acc.status == PaperAccountStatus.ACTIVE
