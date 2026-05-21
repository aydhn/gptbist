import re

filepath = "bist_signal_bot/core/audit.py"
with open(filepath, "r") as f:
    content = f.read()

events = [
    "REVIEW_ITEM_CREATED = \"REVIEW_ITEM_CREATED\"",
    "REVIEW_ITEM_UPDATED = \"REVIEW_ITEM_UPDATED\"",
    "REVIEW_ITEM_ARCHIVED = \"REVIEW_ITEM_ARCHIVED\"",
    "REVIEW_CHECKLIST_CREATED = \"REVIEW_CHECKLIST_CREATED\"",
    "REVIEW_CHECKLIST_UPDATED = \"REVIEW_CHECKLIST_UPDATED\"",
    "REVIEW_THESIS_CREATED = \"REVIEW_THESIS_CREATED\"",
    "REVIEW_THESIS_UPDATED = \"REVIEW_THESIS_UPDATED\"",
    "REVIEW_DECISION_CREATED = \"REVIEW_DECISION_CREATED\"",
    "REVIEW_FOLLOWUP_SET = \"REVIEW_FOLLOWUP_SET\"",
    "REVIEW_FOLLOWUP_CLEARED = \"REVIEW_FOLLOWUP_CLEARED\"",
    "REVIEW_JOURNAL_ENTRY_CREATED = \"REVIEW_JOURNAL_ENTRY_CREATED\"",
    "REVIEW_ITEM_EXPIRED = \"REVIEW_ITEM_EXPIRED\""
]

if "REVIEW_ITEM_CREATED" not in content:
    # insert into AuditEventType
    insert_str = "\n    ".join(events) + "\n"
    content = re.sub(r'(class AuditEventType\(str, Enum\):.*?)(?=\n\n|\Z)', r'\1\n    ' + insert_str, content, flags=re.DOTALL)

    with open(filepath, "w") as f:
        f.write(content)
