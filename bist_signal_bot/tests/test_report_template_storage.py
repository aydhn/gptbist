
from bist_signal_bot.report_templates.storage import ReportTemplateStore
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind
import pytest

def test_save_and_load_templates(tmp_path):
    store = ReportTemplateStore(base_dir=tmp_path)
    t = ReportTemplate(template_id="t1", name="test", kind=ReportTemplateKind.CUSTOM, version="1", description="")
    store.save_templates([t])
    loaded = store.load_templates()
    assert len(loaded) == 1
    assert loaded[0].template_id == "t1"
