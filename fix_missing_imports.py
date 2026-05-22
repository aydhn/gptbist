import os
import glob
import re

files_to_fix = [
    "bist_signal_bot/tests/test_backtest_engine.py",
    "bist_signal_bot/tests/test_backtest_execution.py",
    "bist_signal_bot/tests/test_backtest_models.py",
    "bist_signal_bot/tests/test_backtest_portfolio.py",
    "bist_signal_bot/tests/test_backtest_reporting.py",
    "bist_signal_bot/tests/test_backtest_reports.py",
    "bist_signal_bot/tests/test_backtest_risk_integration.py",
    "bist_signal_bot/tests/test_grid_search_optimizer.py",
    "bist_signal_bot/tests/test_objective_functions.py",
    "bist_signal_bot/tests/test_optimization_engine.py",
    "bist_signal_bot/tests/test_optimization_models.py",
    "bist_signal_bot/tests/test_optimization_reporting.py",
    "bist_signal_bot/tests/test_optimization_storage.py",
    "bist_signal_bot/tests/test_random_search_optimizer.py",
    "bist_signal_bot/tests/test_review_evidence.py",
    "bist_signal_bot/tests/test_review_inbox.py",
    "bist_signal_bot/tests/test_search_space.py",
    "bist_signal_bot/tests/test_walk_forward_optimizer.py"
]

for file_path in files_to_fix:
    if not os.path.exists(file_path): continue

    with open(file_path, "r") as f:
        content = f.read()

    has_optional = "Optional[" in content or " Optional" in content
    has_any = "Any[" in content or " Any" in content or "-> Any" in content

    imports = []
    if has_optional and "from typing import Optional" not in content and "import Optional" not in content:
        imports.append("Optional")
    if has_any and "from typing import Any" not in content and "import Any" not in content:
        imports.append("Any")

    if imports:
        import_stmt = f"from typing import {', '.join(imports)}\n"
        with open(file_path, "w") as f:
            f.write(import_stmt + content)
        print(f"Fixed {file_path}")
