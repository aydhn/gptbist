from bist_signal_bot.factors.models import FactorReport, FactorExposure, FactorScore, FactorType, FactorStatus, FactorExposureDirection
from bist_signal_bot.factors.reporting import format_factor_report_markdown

def test_report_gen():
    r = FactorReport(report_id="123", symbol="ASELS")
    r.exposures.append(
        FactorExposure(
            exposure_id="e1", object_type="SYMBOL", object_id="ASELS",
            aggregate_factor_score=68.0, dominant_factors=["MOMENTUM", "QUALITY"], weak_factors=["VALUE"]
        )
    )
    md = format_factor_report_markdown(r)
    print(md)

test_report_gen()
