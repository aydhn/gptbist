from datetime import datetime
import tempfile
from pathlib import Path
from bist_signal_bot.breadth.storage import BreadthStore
from bist_signal_bot.breadth.models import BreadthSnapshot

def test_breadth_storage():
    with tempfile.TemporaryDirectory() as td:
        store = BreadthStore(base_dir=Path(td))
        snap = BreadthSnapshot(
            snapshot_id="test1",
            as_of_date=datetime(2024,1,1),
            universe_name="U",
            symbols=["S1"]
        )
        p = store.save_snapshot(snap)
        assert p.exists()

        loaded = store.load_latest_snapshot()
        assert loaded is not None
        assert loaded.snapshot_id == "test1"
        assert loaded.symbols == ["S1"]
