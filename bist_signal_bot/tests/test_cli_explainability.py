import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import argparse
from bist_signal_bot.cli.explain import setup_parser, handle_explain

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_explain_signal_cli(capsys):
    args = DummyArgs(explain_cmd="signal", symbol="ASELS", strategy="moving_average_trend", signal_id=None, json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain signal mock for symbol=ASELS, strategy=moving_average_trend" in captured.out

def test_explain_strategy_cli(capsys):
    args = DummyArgs(explain_cmd="strategy", strategy_name="moving_average_trend", symbol="ASELS", json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain strategy mock for moving_average_trend, symbol=ASELS" in captured.out

def test_explain_ensemble_cli(capsys):
    args = DummyArgs(explain_cmd="ensemble", symbol="ASELS", json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain ensemble mock for symbol=ASELS" in captured.out

def test_explain_trace_cli(capsys):
    args = DummyArgs(explain_cmd="trace", symbol="ASELS", strategy="trend", trace_id="123", json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain trace mock for symbol=ASELS, trace_id=123" in captured.out

def test_explain_card_cli(capsys):
    args = DummyArgs(explain_cmd="card", symbol="ASELS", strategy="trend", signal_id=None, card_id="c1", json=False, save=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain card mock for symbol=ASELS, card_id=c1" in captured.out

def test_explain_recent_cli(capsys):
    args = DummyArgs(explain_cmd="recent", symbol="ASELS", json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain recent mock for symbol=ASELS" in captured.out

def test_explain_report_cli(capsys):
    args = DummyArgs(explain_cmd="report", latest=True, json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain report mock" in captured.out

def test_explain_config_cli(capsys):
    args = DummyArgs(explain_cmd="config", json=False)
    handle_explain(args)
    captured = capsys.readouterr()
    assert "Explain config mock" in captured.out
