import pytest
from unittest.mock import patch
import argparse
from bist_signal_bot.cli.commands import handle_data_v2_command
from bist_signal_bot.config.settings import Settings

def test_cli_data_fetch_v2():
    args = argparse.Namespace(
        data_command="fetch-v2",
        symbols=["ASELS"],
        timeframe="1d",
        source="local_file",
        provider_order=None,
        json=False
    )

    with patch('bist_signal_bot.data.data_service.MarketDataService.fetch_v2') as mock_fetch:
        handle_data_v2_command(args, Settings())
        mock_fetch.assert_called_once()

def test_cli_data_freshness():
    args = argparse.Namespace(
        data_command="freshness",
        symbols=["ASELS"],
        timeframe="1d",
        max_age_hours=48.0,
        json=False
    )

    with patch('bist_signal_bot.data.data_service.MarketDataService.freshness_report') as mock_fresh:
        handle_data_v2_command(args, Settings())
        mock_fresh.assert_called_once()

def test_cli_data_lineage():
    args = argparse.Namespace(
        data_command="lineage",
        symbol="ASELS",
        json=False
    )

    with patch('bist_signal_bot.data.data_service.MarketDataService.lineage_summary') as mock_lin:
        handle_data_v2_command(args, Settings())
        mock_lin.assert_called_once()
