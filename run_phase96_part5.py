import os
import re

# Update README.md
try:
    with open("README.md", "r") as f:
        readme_content = f.read()

    if "Research Monitoring" not in readme_content:
        monitoring_section = """
## Research Monitoring (Phase 96)
- **Monitoring amacı**: Strateji ve modellerin sağlık durumunu araştırma amaçlı izler.
- **Strategy/model health**: Performans düşüşlerini skorlar ile takip eder.
- **Performance decay**: Baseline'a göre sapmaları tespit eder.
- **Calibration decay**: Kalibrasyon parametrelerindeki bozulmaları saptar.
- **Champion/challenger**: Yeni stratejileri mevcutları ile araştırma çerçevesinde karşılaştırır.
- **Alerts/watchlist**: İzlenmesi gereken uyarıları bildirir.
- **Review workflow entegrasyonu**: Kritik düşüşlerde Analyst Review ister.
- **QA/Ops entegrasyonu**: İzleme skorları QA release gate testlerini etkiler.
- **CLI monitoring kullanımı**: CLI ile `python -m bist_signal_bot monitoring` ile izleme yapılabilir.
"""
        with open("README.md", "a") as f:
            f.write(monitoring_section)
except Exception as e:
    print(f"Error updating README: {e}")

# Create docs/72_RESEARCH_MONITORING_AND_CHAMPION_CHALLENGER.md
with open("bist_signal_bot/docs/72_RESEARCH_MONITORING_AND_CHAMPION_CHALLENGER.md", "w") as f:
    f.write("""# Research Monitoring and Champion/Challenger V1
## Architecture
- Local-first, JSONL based monitoring
- Research-only: No real trading orders or signals
## Components
- Monitoring Object Types: STRATEGY, MODEL, FEATURE_SET etc.
- Metrics: Win rate, Expectancy, Profit Factor, Drawdown, Calibration Reliability
- Decay Detection: Detects drops below dynamic or static thresholds
- Champion/Challenger Logic: Safe comparison metadata.
- Alerts and escalation: Generates internal alerts, escalates to Review Workflow
- Watchlist: Tracks degraded objects
## Integrations
- Strategy Registry
- Model Registry
- Feature Store
- Review Workflow
- QA / Ops
## Safe Language
- Output must explicitly declare it is for research-only and not financial advice.
## Troubleshooting
- If alerts appear stuck, clear the watchlist via CLI.
""")

# Create examples/monitoring_workflow.md
with open("bist_signal_bot/examples/monitoring_workflow.md", "w") as f:
    f.write("""# Monitoring Workflow Examples
```bash
python -m bist_signal_bot monitoring status
python -m bist_signal_bot monitoring run --object-type STRATEGY --object-id moving_average_trend
python -m bist_signal_bot monitoring decay --object-type STRATEGY --object-id moving_average_trend
python -m bist_signal_bot monitoring champion-challenger --object-type STRATEGY --champion moving_average_trend --challenger breakout_trend
python -m bist_signal_bot monitoring alerts
python -m bist_signal_bot monitoring watchlist
python -m bist_signal_bot monitoring report
```
""")

print("Part 5 done")
