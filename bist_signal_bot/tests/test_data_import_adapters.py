import pytest
import sqlite3
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


def test_sqlite_injection_preview(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create a table with a malicious name
    malicious_table_name = 'users"; DROP TABLE users; --'

    safe_creation_name = malicious_table_name.replace('"', '""')
    c.execute(f'CREATE TABLE "{safe_creation_name}" (id INTEGER, name TEXT)')
    c.execute(f'INSERT INTO "{safe_creation_name}" VALUES (1, "test")')
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()
    from bist_signal_bot.core.exceptions import DataImportAdapterError
    with pytest.raises(DataImportAdapterError, match="Invalid table name detected"):
        registry.read_preview(db_path, max_rows=1)

def test_sqlite_injection_dataframe(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create a table with a malicious name
    malicious_table_name = 'users"; DROP TABLE users; --'

    safe_creation_name = malicious_table_name.replace('"', '""')
    c.execute(f'CREATE TABLE "{safe_creation_name}" (id INTEGER, name TEXT)')
    c.execute(f'INSERT INTO "{safe_creation_name}" VALUES (1, "test")')
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()
    from bist_signal_bot.core.exceptions import DataImportAdapterError
    with pytest.raises(DataImportAdapterError, match="Invalid table name detected"):
        registry.read_dataframe(db_path, max_rows=1)

def test_sqlite_read_chunks(tmp_path):
    db_path = tmp_path / "test_chunks.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE "test_table" (id INTEGER, name TEXT)')
    data = [(i, f"test_{i}") for i in range(15)]
    c.executemany('INSERT INTO "test_table" VALUES (?, ?)', data)
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()
    chunks = list(registry.read_chunks(db_path, chunk_size=5))

    assert len(chunks) == 3
    assert len(chunks[0]) == 5
    assert len(chunks[1]) == 5
    assert len(chunks[2]) == 5

def test_sqlite_injection_chunks(tmp_path):
    db_path = tmp_path / "test_inject_chunks.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    malicious_table_name = 'users"; DROP TABLE users; --'
    safe_creation_name = malicious_table_name.replace('"', '""')
    c.execute(f'CREATE TABLE "{safe_creation_name}" (id INTEGER, name TEXT)')
    c.execute(f'INSERT INTO "{safe_creation_name}" VALUES (1, "test")')
    conn.commit()
    conn.close()

    registry = LocalImportAdapterRegistry()
    from bist_signal_bot.core.exceptions import DataImportAdapterError
    with pytest.raises(DataImportAdapterError, match="Invalid table name detected"):
        list(registry.read_chunks(db_path, chunk_size=5))
