from bist_signal_bot.disclosures.storage import DisclosureStore
from bist_signal_bot.disclosures.models import DisclosureRecord
def test_disclosure_store(tmp_path):
    store = DisclosureStore(base_dir=tmp_path)
    r = DisclosureRecord(disclosure_id="1", title="A", body="B", source="C", symbols=["X"])
    store.append_record(r)
    records = store.load_records()
    assert len(records) == 1
