import json
from datetime import date
import pytest
from pydantic import ValidationError

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.corporate_actions import CorporateActionStore
from bist_signal_bot.data.models import CorporateAction, CorporateActionType
from bist_signal_bot.core.exceptions import CorporateActionStoreError

def test_corporate_action_validation_rules():
    # Negative ratio
    with pytest.raises(ValidationError):
        CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.SPLIT, ratio=-1.0)

    # Negative cash
    with pytest.raises(ValidationError):
        CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.CASH_DIVIDEND, cash_amount=-5.0)

    # Valid
    action = CorporateAction(symbol="asels", action_date=date(2025, 7, 1), action_type=CorporateActionType.SPLIT, ratio=2.0)
    assert action.symbol == "ASELS" # normalized

def test_initialize_empty_creates_valid_json(tmp_path):
    settings = Settings(CORPORATE_ACTIONS_DIR_NAME=str(tmp_path.name), CORPORATE_ACTIONS_FILE_NAME="actions.json")
    store = CorporateActionStore(settings, base_dir=tmp_path.parent)

    assert not store.exists()
    store.initialize_empty()
    assert store.exists()

    with open(store.get_actions_file_path(), "r") as f:
        data = json.load(f)

    assert "actions" in data
    assert len(data["actions"]) == 0
    assert "schema_version" in data

def test_add_remove_and_duplicate_validation(tmp_path):
    settings = Settings(CORPORATE_ACTIONS_DIR_NAME=str(tmp_path.name), CORPORATE_ACTIONS_FILE_NAME="actions.json")
    store = CorporateActionStore(settings, base_dir=tmp_path.parent)

    action = CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.SPLIT, ratio=2.0)
    store.add_action(action)

    actions = store.load_actions()
    assert len(actions) == 1

    # Duplicate add
    with pytest.raises(CorporateActionStoreError):
        store.add_action(action)

    # Validation identifies duplicate
    report = store.validate_actions([action, action])
    assert report.duplicate_actions == 1
    assert len(report.issues) == 1
    assert report.issues[0].issue_type == "DUPLICATE_ACTION"

    # Remove
    assert store.remove_action("ASELS", date(2025, 7, 1), CorporateActionType.SPLIT) is True
    assert len(store.load_actions()) == 0
    assert store.remove_action("ASELS", date(2025, 7, 1), CorporateActionType.SPLIT) is False

def test_csv_import_valid_and_invalid(tmp_path):
    csv_content = """symbol,action_date,action_type,ratio,cash_amount,currency,description,source,verified,metadata
ASELS,2025-07-01,SPLIT,2.0,,TRY,Split,manual,true,
THYAO,invalid_date,CASH_DIVIDEND,,1.5,TRY,Div,manual,false,
"""
    csv_file = tmp_path / "import.csv"
    csv_file.write_text(csv_content)

    settings = Settings(CORPORATE_ACTIONS_DIR_NAME="store", CORPORATE_ACTIONS_FILE_NAME="actions.json")
    store = CorporateActionStore(settings, base_dir=tmp_path)

    report = store.import_actions(csv_file)
    assert not report.passed
    assert report.invalid_actions == 1
    assert "Invalid CSV data" in report.issues[0].message

    # Check valid ones got loaded (if merge successful for the valid part - but validate_actions fails the whole thing in current implementation)
    # Actually, import_actions only saves if report.passed is True. So let's check it didn't save.
    assert len(store.load_actions()) == 0

    # Valid only
    valid_csv = """symbol,action_date,action_type,ratio,cash_amount,currency,description,source,verified,metadata
ASELS,2025-07-01,SPLIT,2.0,,TRY,Split,manual,true,
"""
    csv_file.write_text(valid_csv)
    report = store.import_actions(csv_file)
    assert report.passed

    actions = store.load_actions()
    assert len(actions) == 1
    assert actions[0].symbol == "ASELS"
    assert actions[0].ratio == 2.0
