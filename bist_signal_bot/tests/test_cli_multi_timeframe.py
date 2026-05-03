import pytest
from unittest.mock import MagicMock
from bist_signal_bot.cli.commands import cmd_mtf_features
from bist_signal_bot.app.bootstrap import ApplicationContext
from bist_signal_bot.config.settings import Settings
import argparse

def test_cmd_mtf_features_basic():
    ctx = MagicMock(spec=ApplicationContext)
    ctx.settings = Settings()
    ctx.audit_logger = MagicMock()

    args = argparse.Namespace(
        command="mtf-features",
        symbol="TEST",
        source="mock",
        base_timeframe="1d",
        higher=None,
        period=None,
        rows=100,
        level="basic",
        alignment_mode=None,
        no_forward_fill=False,
        no_shift_higher_tf=False,
        drop_unaligned=False,
        save_output=False,
        json=False
    )

    ret = cmd_mtf_features(args, ctx)
    assert ret == 0

def test_cmd_mtf_features_json():
    ctx = MagicMock(spec=ApplicationContext)
    ctx.settings = Settings()
    ctx.audit_logger = MagicMock()

    args = argparse.Namespace(
        command="mtf-features",
        symbol="TEST",
        source="mock",
        base_timeframe="1d",
        higher=["1wk", "1mo"],
        period=None,
        rows=100,
        level="full",
        alignment_mode=None,
        no_forward_fill=False,
        no_shift_higher_tf=False,
        drop_unaligned=False,
        save_output=False,
        json=True
    )

    ret = cmd_mtf_features(args, ctx)
    assert ret == 0
