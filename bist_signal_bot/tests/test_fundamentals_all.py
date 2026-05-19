import pytest
from datetime import datetime
from bist_signal_bot.fundamentals.models import FinancialStatementRecord, FinancialStatementType, FinancialPeriodType, FundamentalDataStatus, CorporateEvent, CorporateEventType, FundamentalImportRequest
from bist_signal_bot.fundamentals.storage import FundamentalStore
from bist_signal_bot.fundamentals.importers import FundamentalDataImporter
from bist_signal_bot.fundamentals.ratios import FundamentalRatioCalculator
from bist_signal_bot.fundamentals.factors import FactorScorer
from bist_signal_bot.fundamentals.engine import FundamentalEngine
from bist_signal_bot.fundamentals.filters import FundamentalSignalFilter, SignalCandidate

@pytest.fixture
def store(tmp_path): return FundamentalStore(tmp_path)

def test_financial_statement_record_validation():
    rec = FinancialStatementRecord(record_id="test", symbol="asels", statement_type=FinancialStatementType.INCOME_STATEMENT, period_type=FinancialPeriodType.QUARTERLY, fiscal_year=2024, period_end_date=datetime.now(), currency="TRY", values={"revenue": 100}, imported_at=datetime.now())
    assert rec.symbol == "ASELS"

def test_corporate_event_validation():
    evt = CorporateEvent(event_id="test", symbol="ASELS", event_type=CorporateEventType.DIVIDEND, event_date=datetime.now(), description="Test", imported_at=datetime.now(), amount=1.5)
    assert evt.amount == 1.5

def test_importer_csv(store):
    importer = FundamentalDataImporter(store)
    req = FundamentalImportRequest(input_path="dummy", import_type="statements")
    res = importer.import_financial_statements(req)
    assert res.status == FundamentalDataStatus.VALID

def test_ratio_calculator():
    calc = FundamentalRatioCalculator()
    rec = FinancialStatementRecord(record_id="1", symbol="ASELS", statement_type=FinancialStatementType.UNKNOWN, period_type=FinancialPeriodType.QUARTERLY, fiscal_year=2024, period_end_date=datetime.now(), currency="TRY", values={"revenue": 100}, imported_at=datetime.now())
    snap = calc.calculate_ratios("ASELS", [rec])
    assert snap.ratios["net_margin"] == 0.2

def test_factor_scorer():
    calc = FundamentalRatioCalculator()
    rec = FinancialStatementRecord(record_id="1", symbol="ASELS", statement_type=FinancialStatementType.UNKNOWN, period_type=FinancialPeriodType.QUARTERLY, fiscal_year=2024, period_end_date=datetime.now(), currency="TRY", values={"revenue": 100}, imported_at=datetime.now())
    snap = calc.calculate_ratios("ASELS", [rec])
    scorer = FactorScorer()
    scores = scorer.score_symbol("ASELS", snap)
    comp = next(s for s in scores if s.factor_group.value == "COMPOSITE")
    assert comp.score > 0

def test_fundamental_filter():
    filter = FundamentalSignalFilter()
    sig = SignalCandidate("ASELS", 0.5)
    from bist_signal_bot.fundamentals.models import FundamentalScorecard
    card = FundamentalScorecard(symbol="ASELS", as_of_date=datetime.now(), available_at=datetime.now(), composite_score=80.0, data_status=FundamentalDataStatus.VALID)
    decision, out_sig, warnings = filter.filter_signal(sig, card, mode="score_adjust")
    assert out_sig.score > 0.5

def test_fundamental_engine(store):
    engine = FundamentalEngine.from_settings()
    card = engine.build_scorecard("ASELS")
    assert card.composite_score == 50.0
