import re

health_path = "bist_signal_bot/app/healthcheck.py"
with open(health_path, "r") as f:
    content = f.read()

# We need to add the financials key to the JSON output, and also print it if not JSON.
content = content.replace('        "disclosures": {', '''        "financials": {
            "enabled": getattr(settings, "ENABLE_FINANCIALS", True),
            "importer_capable": True,
            "normalizer_capable": True,
            "ratio_capable": True,
            "quality_capable": True,
            "store_capable": True
        },
        "disclosures": {''')

content = content.replace('    print(f"Disclosure Intelligence Enabled: {res[\'disclosures\'][\'enabled\']}")', '''    print(f"Disclosure Intelligence Enabled: {res['disclosures']['enabled']}")
    print(f"Financials enabled: {res['financials']['enabled']}")''')

with open(health_path, "w") as f:
    f.write(content)

test_path = "bist_signal_bot/tests/test_financial_fundamentals_integration.py"
with open(test_path, "r") as f:
    content2 = f.read()
content2 = content2.replace("from bist_signal_bot.financials.storage import FinancialStore", "from bist_signal_bot.financials.storage import FinancialStore\nfrom pathlib import Path")
with open(test_path, "w") as f:
    f.write(content2)
