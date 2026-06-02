import pytest
from pathlib import Path
from bist_signal_bot.data_import.chunking import ImportChunkReader
from bist_signal_bot.config.settings import Settings

def test_chunk_count_estimate(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n5,6")
    reader = ImportChunkReader(Settings())
    assert reader.chunk_count_estimate(csv_path, chunk_size=2) == 2

def test_combine_chunk_summaries():
    reader = ImportChunkReader(Settings())
    summaries = [
        {"duplicate_rows_removed": 1, "invalid_rows_removed": 2},
        {"duplicate_rows_removed": 3, "invalid_rows_removed": 0}
    ]
    comb = reader.combine_chunk_summaries(summaries)
    assert comb["duplicate_rows_removed"] == 4
    assert comb["invalid_rows_removed"] == 2
