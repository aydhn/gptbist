
from bist_signal_bot.whatif.reporting import format_whatif_report_markdown
from bist_signal_bot.whatif.models import WhatIfRunResult, WhatIfRunRequest, WhatIfStatus

def test_reporting():
    req = WhatIfRunRequest(request_id="1", source_type="test")
    res = WhatIfRunResult(run_id="run1", request=req, elapsed_seconds=1.0, status=WhatIfStatus.PASS)
    md = format_whatif_report_markdown(res)
    assert "run1" in md
