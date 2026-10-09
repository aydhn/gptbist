import pytest

from bist_signal_bot.cli.intraday_cli import build_parser


def test_intraday_parser_commands():
    p = build_parser()
    assert p.parse_args(["archive-update", "--interval", "15m", "--symbols", "THYAO"]).symbols == ["THYAO"]
    assert p.parse_args(["gaps", "THYAO", "--days", "5"]).days == 5
    assert p.parse_args(["status"]).intraday_command == "status"


def test_archive_update_symbol_options_are_exclusive():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["archive-update", "--symbols", "A", "--all-active"])
