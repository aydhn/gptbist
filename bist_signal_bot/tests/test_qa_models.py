
from bist_signal_bot.qa.models import QAFixtureManifest, QAScenario, QAScenarioKind, QAStatus, QACheckResult, QAModuleName, QACheckType
import uuid
from datetime import datetime

def test_qa_models():
    man = QAFixtureManifest(manifest_id="123", created_at=datetime.utcnow(), fixture_root=".")
    assert man.manifest_id == "123"

    scen = QAScenario(scenario_id="1", scenario_kind=QAScenarioKind.BASELINE, name="x", description="y", expected_status=QAStatus.PASS)
    assert "QA scenario is synthetic research test metadata only" in scen.disclaimer

    chk = QACheckResult(check_id="1", check_type=QACheckType.UNIT, module_name=QAModuleName.CORE, name="z", status=QAStatus.PASS, started_at=datetime.utcnow())
    assert chk.status == QAStatus.PASS
