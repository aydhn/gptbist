import pytest
from pathlib import Path
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.data_import.models import ImportSourceFormat

def test_infer_format_csv(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("a,b\n1,2")
    registry = LocalImportAdapterRegistry()
    assert registry.infer_format(csv_path) == ImportSourceFormat.CSV

def test_infer_format_jsonl(tmp_path):
    jsonl_path = tmp_path / "test.jsonl"
    jsonl_path.write_text('{"a": 1}\n{"a": 2}')
    registry = LocalImportAdapterRegistry()
    assert registry.infer_format(jsonl_path) == ImportSourceFormat.JSONL

def test_read_preview_csv(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("col1,col2\nval1,val2\nval3,val4")
    registry = LocalImportAdapterRegistry()
    preview = registry.read_preview(csv_path, max_rows=1)
    assert len(preview) == 1
    assert preview[0]["col1"] == "val1"

def test_unsupported_format(tmp_path):
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("dummy")
    registry = LocalImportAdapterRegistry()
    assert registry.infer_format(txt_path) == ImportSourceFormat.UNKNOWN

import sqlite3
import pandas as pd

def test_sqlite_injection_table_name(tmp_path):
    # Test that a tricky table name (which might be used for SQL injection)
    # is correctly escaped and does not throw syntax errors.
    db_path = tmp_path / "test_malicious.sqlite"

    conn = sqlite3.connect(db_path)
    # Create a table with double quotes and spaces in its name
    tricky_name = 'malicious" table'
    safe_name = tricky_name.replace('"', '""')
    conn.execute(f'CREATE TABLE "{safe_name}" (id int)')
    safe_name = tricky_name.replace('"', '""')
    conn.execute(f'INSERT INTO "{safe_name}" VALUES (1)')
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()

    # Try reading dataframe
    df = registry.read_dataframe(db_path, max_rows=10)
    assert len(df) == 1
    assert df.iloc[0]["id"] == 1

    # Try reading preview
    preview = registry.read_preview(db_path, max_rows=10)
    assert len(preview) == 1
    assert preview[0]["id"] == 1
