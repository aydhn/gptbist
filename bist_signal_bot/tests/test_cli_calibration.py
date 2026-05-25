import bist_signal_bot.cli.calibration_cli
import pytest
import json
from unittest.mock import patch
from bist_signal_bot.cli.main import run_cli

@patch("bist_signal_bot.cli.calibration_cli.create_calibration_store")
@patch("bist_signal_bot.cli.calibration_cli.create_outcome_dataset_builder")
def test_cli_build_outcomes(mock_builder, mock_store, capsys):
    mock_builder.return_value.build_dataset.return_value = []

    run_cli(["calibration", "build-outcomes", "--json"])

    out, err = capsys.readouterr()
    res = json.loads(out)
    assert res["status"] == "success"
    assert res["count"] == 0
