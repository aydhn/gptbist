import pytest
from bist_signal_bot.final_audit.integration_matrix import FinalIntegrationMatrixBuilder
from bist_signal_bot.final_audit.models import FinalAuditStatus, FinalIntegrationMatrixItem

def test_integration_matrix_builder_default_pairs():
    builder = FinalIntegrationMatrixBuilder()
    matrix = builder.build_matrix()
    assert len(matrix.items) > 10

    # Check required pair
    qa_ops = [i for i in matrix.items if i.source_module == "qa" and i.target_module == "ops"]
    assert len(qa_ops) == 1

def test_required_failures_produce_fail_status():
    builder = FinalIntegrationMatrixBuilder()
    item = FinalIntegrationMatrixItem(
        item_id="1", source_module="a", target_module="b", integration_name="test",
        required=True, latest_status=FinalAuditStatus.FAIL
    )
    assert builder.matrix_status([item]) == FinalAuditStatus.FAIL
