import pytest
from bist_signal_bot.reports.digest import ReportDigestBuilder
from bist_signal_bot.reports.models import GeneratedReport, ReportType, ReportStatus, ReportAudience
from bist_signal_bot.config.settings import Settings

class MockNotifier:
    def __init__(self):
        self.sent = False
    def send_message(self, message):
        self.sent = True

def test_build_telegram_digest():
    settings = Settings(REPORT_DIGEST_MAX_CHARS=100)
    builder = ReportDigestBuilder(settings=settings)
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test"
    )
    digest = builder.build_telegram_digest(report)
    assert digest.title == "Digest for Test"
    assert "DAILY" in digest.message

def test_send_digest_requires_confirm():
    settings = Settings(REPORT_TELEGRAM_DIGEST_ENABLED=True, REPORT_TELEGRAM_REQUIRE_CONFIRM=True)
    builder = ReportDigestBuilder(settings=settings)
    report = GeneratedReport(report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL, status=ReportStatus.SUCCESS, title="Test")
    digest = builder.build_telegram_digest(report)

    with pytest.raises(Exception):
        builder.send_digest(digest, MockNotifier(), confirm=False)

def test_send_digest_disabled():
    settings = Settings(REPORT_TELEGRAM_DIGEST_ENABLED=False)
    builder = ReportDigestBuilder(settings=settings)
    report = GeneratedReport(report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL, status=ReportStatus.SUCCESS, title="Test")
    digest = builder.build_telegram_digest(report)

    res = builder.send_digest(digest, MockNotifier())
    assert not res.sent
    assert "disabled" in res.warnings[0]

class MockFailingNotifier:
    def send_message(self, message):
        raise Exception("Mock notification failure")

def test_send_digest_failure():
    settings = Settings(REPORT_TELEGRAM_DIGEST_ENABLED=True, REPORT_TELEGRAM_REQUIRE_CONFIRM=False)
    builder = ReportDigestBuilder(settings=settings)
    report = GeneratedReport(
        report_id="fail_test_1",
        report_type=ReportType.DAILY,
        audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS,
        title="Failure Test"
    )
    digest = builder.build_telegram_digest(report)

    notifier = MockFailingNotifier()
    res = builder.send_digest(digest, notifier)

    assert not res.sent
    assert res.status == ReportStatus.FAILED
    assert any("Mock notification failure" in w for w in res.warnings)
