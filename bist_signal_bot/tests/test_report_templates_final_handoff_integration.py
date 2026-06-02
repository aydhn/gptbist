
from bist_signal_bot.final_handoff.release_pack import add_report_templates_artifacts

def test_add_report_templates_artifacts():
    pack = {"artifacts": []}
    res = add_report_templates_artifacts(pack)
    assert res == pack
