import pytest
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.paper.account import PaperAccountManager
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperLedgerError

def test_ledger_initialize_file(tmp_path):
    # 9. Ledger initialize dosya oluşturur.
    settings = Settings()
    store = PaperLedgerStore(settings, base_dir=tmp_path)
    manager = PaperAccountManager(settings)

    acc = manager.create_account(initial_cash=5000, account_id="acc1")
    state = store.initialize_ledger(acc)

    assert store.get_ledger_path("acc1").exists()

def test_ledger_save_load(tmp_path):
    # 10. Ledger save/load state korur.
    settings = Settings()
    store = PaperLedgerStore(settings, base_dir=tmp_path)
    manager = PaperAccountManager(settings)

    acc = manager.create_account(initial_cash=5000, account_id="acc1")
    state = store.initialize_ledger(acc)

    acc.cash = 4000
    store.save(state)

    loaded = store.load("acc1")
    assert loaded.account.cash == 4000

def test_ledger_corrupted_json(tmp_path):
    # 11. Ledger bozuk JSON’da PaperLedgerError üretir.
    settings = Settings()
    store = PaperLedgerStore(settings, base_dir=tmp_path)
    manager = PaperAccountManager(settings)
    acc = manager.create_account(initial_cash=5000, account_id="acc1")
    store.initialize_ledger(acc)

    p = store.get_ledger_path("acc1")
    with open(p, "w") as f:
        f.write("{invalid json")

    with pytest.raises(PaperLedgerError):
        store.load("acc1")

def test_ledger_export_csv(tmp_path):
    # 12. Ledger export_csv dosyaları oluşturur.
    settings = Settings()
    store = PaperLedgerStore(settings, base_dir=tmp_path)
    manager = PaperAccountManager(settings)

    acc = manager.create_account(initial_cash=5000, account_id="acc1")
    state = store.initialize_ledger(acc)

    paths = store.export_csv(state)
    assert "orders" in paths
    assert paths["orders"].exists()
    assert paths["fills"].exists()
