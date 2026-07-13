🧪 Add test for cmd_valuation_risk

* 🎯 **What:** The `cmd_valuation_risk` function in `bist_signal_bot/cli/valuation_commands.py` lacked a unit test.
* 📊 **Coverage:** A new test `test_cmd_valuation_risk` was added to `bist_signal_bot/tests/test_cli_valuation.py` that verifies the function properly delegates execution to `cmd_valuation_show` with the correct arguments and returns the result.
* ✨ **Result:** Increased test coverage and ensures future refactoring won't break the delegation logic.
