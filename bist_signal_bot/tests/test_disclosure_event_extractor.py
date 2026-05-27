from datetime import datetime
from bist_signal_bot.disclosures.event_extractor import DisclosureEventExtractor
from bist_signal_bot.disclosures.models import DisclosureRecord
def test_extract_dates():
    ext = DisclosureEventExtractor()
    rec = DisclosureRecord(disclosure_id="1", title="A", body="Toplantı 15.08.2023 tarihinde.", source="c")
    extractions = ext.extract_events(rec)
    assert len(extractions) == 1
    assert extractions[0].event_date.year == 2023
