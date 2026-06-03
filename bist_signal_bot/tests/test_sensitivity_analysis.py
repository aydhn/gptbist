from bist_signal_bot.explainability.sensitivity import SensitivityAnalysisEngine

class MockModel:
    def predict(self, rows):
        return [float(r.get("f1", 0) * 2) for r in rows]

def test_sensitivity_numeric():
    engine = SensitivityAnalysisEngine()
    row = {"f1": 10.0}
    res = engine.analyze_feature(MockModel(), row, "f1")
    assert res.status.value == "PASS"
    assert len(res.points) == 4

def test_sensitivity_non_numeric():
    engine = SensitivityAnalysisEngine()
    row = {"f1": "str"}
    res = engine.analyze_feature(MockModel(), row, "f1")
    assert res.status.value == "WATCH"
    assert "Non-numeric" in res.warnings[0]

def test_sensitivity_monotonicity():
    engine = SensitivityAnalysisEngine()
    row = {"f1": 10.0}
    res = engine.analyze_feature(MockModel(), row, "f1", perturbations=[5.0, 10.0, 15.0])
    assert res.monotonicity_hint == "Monotonically Increasing"
