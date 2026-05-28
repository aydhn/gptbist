
from bist_signal_bot.factors.storage import FactorStore
from bist_signal_bot.factors.models import FactorExposure
import tempfile
from pathlib import Path

def test_factor_storage():
    with tempfile.TemporaryDirectory() as td:
        s = FactorStore(base_dir=Path(td))
        e = FactorExposure(exposure_id="1", object_type="test", object_id="1")
        p = s.append_exposure(e)
        assert p.exists()
