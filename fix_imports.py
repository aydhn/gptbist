with open("bist_signal_bot/tests/test_scanner_storage.py", "r") as f:
    content = f.read()

# Replace multiple from models imports with one
content = content.replace("from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode",
                        "from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode, ScanRankingItem, SymbolScanResult, ScanCandidateStatus, SymbolScanIssue, ScanStatus")
content = content.replace("from bist_signal_bot.scanner.models import ScanStatus\n", "")
content = content.replace("from bist_signal_bot.scanner.models import ScanRankingItem, SymbolScanResult, ScanCandidateStatus, SymbolScanIssue\n", "")

# Fix json import
content = content.replace("import json\n", "")
content = "import json\n" + content

with open("bist_signal_bot/tests/test_scanner_storage.py", "w") as f:
    f.write(content)
