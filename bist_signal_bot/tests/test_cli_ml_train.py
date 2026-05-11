import pytest
import argparse
from bist_signal_bot.cli.parsers import setup_ml_train_parser

def test_ml_train_cli_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    setup_ml_train_parser(subparsers)

    args = parser.parse_args(["ml-train", "train", "--symbols", "ASELS", "--target", "lbl"])

    assert args.command == "ml-train"
    assert args.ml_train_command == "train"
    assert args.symbols == ["ASELS"]
    assert args.target == "lbl"

def test_ml_train_predict_cli_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    setup_ml_train_parser(subparsers)

    args = parser.parse_args(["ml-train", "predict", "--model-id", "test_id", "--symbols", "ASELS"])

    assert args.command == "ml-train"
    assert args.ml_train_command == "predict"
    assert args.model_id == "test_id"
    assert args.symbols == ["ASELS"]
