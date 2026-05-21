import pytest
from bist_signal_bot.maintenance.doctor import MaintenanceDoctor

def test_maintenance_doctor_required_dirs(tmp_path):
    doctor = MaintenanceDoctor(tmp_path)
    missing = doctor.check_required_dirs()
    assert len(missing) > 0
    assert "logs" in missing
    assert "reports" in missing

def test_maintenance_doctor_jsonl_integrity(tmp_path):
    doctor = MaintenanceDoctor(tmp_path)

    good_jsonl = tmp_path / "good.jsonl"
    good_jsonl.write_text('{"a": 1}\n{"b": 2}')

    bad_jsonl = tmp_path / "bad.jsonl"
    bad_jsonl.write_text('{"a": 1}\n{bad_json}')

    corrupted = doctor.check_jsonl_integrity([good_jsonl, bad_jsonl])

    assert len(corrupted) == 1
    assert "bad.jsonl" in corrupted[0]

def test_maintenance_doctor_secret_risk(tmp_path):
    doctor = MaintenanceDoctor(tmp_path)

    secret_file = tmp_path / "my_secret.txt"
    secret_file.touch()

    risks = doctor.check_secret_risk([secret_file])

    assert len(risks) == 1
    assert "my_secret.txt" in risks[0]
