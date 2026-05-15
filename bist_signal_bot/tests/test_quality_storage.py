import pytest
import json
from bist_signal_bot.quality.storage import QualityReportStore
from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus

def test_save_json(tmp_path):
    store = QualityReportStore()
    config = QualityRunConfig()
    result = QualityRunResult(run_id="test-123", config=config, status=QualityCheckStatus.PASS)

    path = store.save_json(result, output_dir=tmp_path)
    assert path.exists()

    with open(path) as f:
        data = json.load(f)
        assert data["run_id"] == "test-123"

def test_save_markdown(tmp_path):
    store = QualityReportStore()
    config = QualityRunConfig()
    result = QualityRunResult(run_id="test-123", config=config, status=QualityCheckStatus.PASS, disclaimer="Test disclaimer")

    path = store.save_markdown(result, output_dir=tmp_path)
    assert path.exists()

    content = path.read_text()
    assert "test-123" in content
    assert "Test disclaimer" in content

def test_save_checks_csv(tmp_path):
    store = QualityReportStore()
    config = QualityRunConfig()
    result = QualityRunResult(run_id="test-123", config=config, status=QualityCheckStatus.PASS)

    path = store.save_checks_csv(result, output_dir=tmp_path)
    assert path.exists()

    content = path.read_text()
    assert "check_name" in content

def test_list_recent_runs(tmp_path):
    store = QualityReportStore()
    # Mocking get_quality_dir to point to tmp_path
    store.get_quality_dir = lambda: tmp_path

    run_dir = tmp_path / "20230101" / "test-123"
    run_dir.mkdir(parents=True)
    summary_path = run_dir / "summary.json"
    with open(summary_path, "w") as f:
         json.dump({"run_id": "test-123", "status": "PASS"}, f)

    runs = store.list_recent_quality_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "test-123"
