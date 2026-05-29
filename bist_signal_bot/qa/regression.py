from bist_signal_bot.qa.models import RegressionMatrixResult, RegressionMatrixItem, QAStatus, QAModuleName, QACheckType
import uuid
from datetime import datetime

class RegressionMatrixBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def default_matrix(self) -> list[RegressionMatrixItem]:
        return [
            RegressionMatrixItem(
                item_id=str(uuid.uuid4()),
                module_name=QAModuleName.CORE,
                check_type=QACheckType.UNIT,
                test_name="core_tests",
                required_for_release=True,
                expected_status=QAStatus.PASS
            )
        ]

    def build_matrix(self, latest_results=None) -> RegressionMatrixResult:
        items = self.default_matrix()
        if latest_results:
            items = self.mark_latest_status(items, latest_results)

        return RegressionMatrixResult(
            matrix_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            items=items,
            total_count=len(items),
            pass_count=len([i for i in items if i.latest_status == QAStatus.PASS]),
            status=self.status_from_counts(len(items), 0, 0, 0)
        )

    def mark_latest_status(self, items, results):
        return items

    def required_failures(self, result: RegressionMatrixResult):
        return [i for i in result.items if i.required_for_release and i.latest_status == QAStatus.FAIL]

    def status_from_counts(self, pass_count: int, watch_count: int, fail_count: int, blocked_count: int) -> QAStatus:
        if blocked_count > 0: return QAStatus.BLOCKED
        if fail_count > 0: return QAStatus.FAIL
        if watch_count > 0: return QAStatus.WATCH
        return QAStatus.PASS
