# 🧪 Test `model_card_to_dict` in model registry reporting

## 🎯 What
Added missing unit tests for the `model_card_to_dict` function inside `bist_signal_bot/model_registry/reporting.py`. This function converts complex `ModelCard` objects into flat dictionaries, stripping out unnecessary nested logic and enums into strings, which warrants coverage to prevent silent API response regressions.

## 📊 Coverage
The new tests cover:
- **Happy Path:** Proper conversion of core fields like `model_id`, `model_name`, `version`.
- **Enum Conversion:** Ensures `governance_status` evaluates correctly to its `.value` equivalent (`PASS`, `FAIL`, etc.) instead of serializing the Enum object.
- **Datetime Format:** Verifies that `created_at` successfully transforms into an ISO 8601 formatted string.
- **Optional/Full Serialization:** Checks against extra parameters like `intended_use` and `known_limitations` ensuring no pollution of the expected flat dictionary model.

## ✨ Result
Increased test coverage in `model_registry/reporting.py`, minimizing the risk of silent failures when saving, exchanging, or generating reports with `ModelCard` outputs.
