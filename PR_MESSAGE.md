Title: 🧹 [code health: simplify build_default_schema by extracting helper methods]

Description:
* 🎯 **What:** The `build_default_schema` function in `bist_signal_bot/config_registry/schema.py` was unnecessarily long and repetitive, constructing dozens of config definitions sequentially.
* 💡 **Why:** Refactoring the monolithic function into helper methods (`_get_forbidden_defs`, `_get_sensitive_defs`, etc.) significantly reduces the length of the function, groups related configurations cleanly, and improves the readability and maintainability of the codebase.
* ✅ **Verification:** Re-ran the existing test suite (using `pytest bist_signal_bot/tests/test_config_registry.py`), ensuring 100% success rate to confirm behavior preservation. Checked code manually to ensure exact identical output definition list generation is preserved, down to preserving the subtle order mapping insertion logic for SYSTEM components.
* ✨ **Result:** Improved maintainability, making it much easier to add new groups of definitions and scale out the Config Schema.
