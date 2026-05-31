import os

path = "bist_signal_bot/core/audit.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "MODEL_REGISTERED" not in content:
        hook = """
    # Model Registry
    MODEL_REGISTERED = "MODEL_REGISTERED"
    MODEL_STATUS_UPDATED = "MODEL_STATUS_UPDATED"
    MODEL_ARCHIVED = "MODEL_ARCHIVED"
    EXPERIMENT_RUN_STARTED = "EXPERIMENT_RUN_STARTED"
    EXPERIMENT_RUN_COMPLETED = "EXPERIMENT_RUN_COMPLETED"
    EXPERIMENT_RUN_FAILED = "EXPERIMENT_RUN_FAILED"
    MODEL_ARTIFACT_REGISTERED = "MODEL_ARTIFACT_REGISTERED"
    MODEL_CARD_CREATED = "MODEL_CARD_CREATED"
    MODEL_VALIDATION_SUMMARIZED = "MODEL_VALIDATION_SUMMARIZED"
    MODEL_CALIBRATION_SUMMARIZED = "MODEL_CALIBRATION_SUMMARIZED"
    MODEL_PROMOTION_REQUESTED = "MODEL_PROMOTION_REQUESTED"
    MODEL_PROMOTION_APPROVED_RESEARCH = "MODEL_PROMOTION_APPROVED_RESEARCH"
    MODEL_PROMOTION_REJECTED = "MODEL_PROMOTION_REJECTED"
    MODEL_DRIFT_DETECTED = "MODEL_DRIFT_DETECTED"
    MODEL_LINEAGE_EDGE_CREATED = "MODEL_LINEAGE_EDGE_CREATED"
    MODEL_GOVERNANCE_ASSESSED = "MODEL_GOVERNANCE_ASSESSED"
    MODEL_REGISTRY_REPORT_CREATED = "MODEL_REGISTRY_REPORT_CREATED"
"""
        idx = content.find("class AuditEventType(str, Enum):")
        if idx != -1:
            content = content.replace("class AuditEventType(str, Enum):", "class AuditEventType(str, Enum):" + hook)

    with open(path, "w") as f:
        f.write(content)


path = "bist_signal_bot/notifications/formatter.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "format_model_record" not in content:
        hook = """
    def format_model_record(self, model: Any) -> str:
        return f"BIST Bot Model Registry Özeti\\n\\nModel: {model.model_name}\\nVersion: {model.version}\\nStatus: {model.status.value}\\n\\nBu çıktı yerel model yönetişimi özetidir.\\nYatırım tavsiyesi değildir.\\nİşlem uygunluğu anlamına gelmez.\\nGerçek emir gönderilmedi."
"""
        idx = content.find("class NotificationFormatter:")
        if idx != -1:
            content = content.replace("class NotificationFormatter:", "class NotificationFormatter:" + hook)

    with open(path, "w") as f:
        f.write(content)
