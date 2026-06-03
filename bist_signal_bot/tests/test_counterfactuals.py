from bist_signal_bot.explainability.counterfactuals import CounterfactualResearchEngine

class MockModel:
    def predict(self, rows):
        return [r.get("f1", 0) for r in rows]

def test_counterfactual_output_delta():
    engine = CounterfactualResearchEngine()
    row = {"f1": 10.0}
    cf = engine.generate_counterfactual(MockModel(), row, {"f1": 20.0})
    assert cf.delta_output == 10.0

def test_counterfactual_implausible():
    engine = CounterfactualResearchEngine()
    row = {"f1": 10.0}
    # more than 5x change
    cf = engine.generate_counterfactual(MockModel(), row, {"f1": 60.0})
    assert cf.plausibility_status.value == "WATCH"
    assert "Implausible" in cf.warnings[0]
