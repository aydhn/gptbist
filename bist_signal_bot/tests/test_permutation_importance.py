from bist_signal_bot.explainability.permutation import PermutationImportanceEngine

class MockModel:
    def predict(self, rows):
        return [float(r.get("f1", 0) + r.get("f2", 0)) for r in rows]

def test_permutation_importance_no_mutation():
    engine = PermutationImportanceEngine()
    rows = [{"f1": 10, "f2": 20}, {"f1": 30, "f2": 40}]
    original_f1_0 = rows[0]["f1"]

    engine.permute_feature(rows, "f1")
    assert rows[0]["f1"] == original_f1_0 # Original list should not be mutated

def test_permutation_importance_same_seed():
    engine = PermutationImportanceEngine()
    rows = [{"f1": i} for i in range(10)]

    p1 = engine.permute_feature(rows, "f1", seed=42)
    p2 = engine.permute_feature(rows, "f1", seed=42)

    assert [r["f1"] for r in p1] == [r["f1"] for r in p2]

def test_permutation_importance_fallback():
    engine = PermutationImportanceEngine()
    rows = [{"f1": 10}, {"f1": 20}]

    # Passing an object without predict
    res = engine.compute_importance("not_a_model", rows)
    assert res.status.value == "UNSUPPORTED_MODEL"
