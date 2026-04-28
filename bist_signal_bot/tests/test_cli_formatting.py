import pytest
from datetime import datetime
from enum import Enum
from bist_signal_bot.cli.formatting import to_json_output, format_key_values, safe_float

class MockEnum(Enum):
    VAL1 = "value1"

def test_to_json_output():
    data = {
        "date": datetime(2024, 1, 1, 12, 0, 0),
        "enum": MockEnum.VAL1,
        "string": "test"
    }
    json_str = to_json_output(data)
    assert "2024-01-01T12:00:00" in json_str
    assert "value1" in json_str
    assert "test" in json_str

def test_format_key_values():
    data = {"key1": "val1", "dict1": {"sub1": "subval1"}}
    text = format_key_values(data)
    assert "key1: val1" in text
    assert "dict1:" in text
    assert "  sub1: subval1" in text

def test_safe_float():
    assert safe_float(1.23456) == 1.2346
    assert safe_float("not_float") == "not_float"
