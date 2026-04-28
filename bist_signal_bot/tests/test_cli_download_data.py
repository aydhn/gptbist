import pytest
from argparse import Namespace
from bist_signal_bot.cli.commands import cmd_download_data
from bist_signal_bot.app.bootstrap import bootstrap_app
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def app_context(tmp_path):
    import os
    os.environ["DATA_DIR"] = str(tmp_path)
    os.environ["RUN_MODE"] = "research"
    return bootstrap_app()

def test_cli_download_single(app_context, capsys):
    args = Namespace(
        symbols=["ASELS"],
        all=False,
        group=None,
        timeframe="1d",
        period="2y",
        refresh=False,
        no_save=True,
        continue_on_error=False,
        fail_fast=False,
        telegram_summary=False,
        json=False
    )
    res = cmd_download_data(args, app_context)
    assert res == 0
    out, err = capsys.readouterr()
    assert "Durum: SUCCESS" in out

def test_cli_download_batch(app_context, capsys):
    args = Namespace(
        symbols=["ASELS", "THYAO"],
        all=False,
        group=None,
        timeframe="1d",
        period="2y",
        refresh=False,
        no_save=True,
        continue_on_error=False,
        fail_fast=False,
        telegram_summary=False,
        json=False
    )
    res = cmd_download_data(args, app_context)
    assert res == 0
    out, err = capsys.readouterr()
    assert "Toplu indirme tamamlandı" in out
    assert "success_count: 2" in out

def test_cli_download_no_args(app_context, capsys):
    args = Namespace(
        symbols=[],
        all=False,
        group=None,
        timeframe="1d",
        period="2y",
        refresh=False,
        no_save=True,
        continue_on_error=False,
        fail_fast=False,
        telegram_summary=False,
        json=False
    )
    res = cmd_download_data(args, app_context)
    assert res == 1
    out, err = capsys.readouterr()
    assert "Lütfen symbol" in out

def test_cli_download_all_and_symbols(app_context, capsys):
    args = Namespace(
        symbols=["ASELS"],
        all=True,
        group=None,
        timeframe="1d",
        period="2y",
        refresh=False,
        no_save=True,
        continue_on_error=False,
        fail_fast=False,
        telegram_summary=False,
        json=False
    )
    res = cmd_download_data(args, app_context)
    assert res == 1
    out, err = capsys.readouterr()
    assert "aynı anda kullanılamaz" in out
