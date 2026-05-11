import os

path = "bist_signal_bot/core/audit.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "ML_INFERENCE_COMPLETED" not in content:
        content = content.replace("ML_TRAINING_FAILED = \"ML_TRAINING_FAILED\"", "ML_TRAINING_FAILED = \"ML_TRAINING_FAILED\"\n    ML_INFERENCE_STARTED = \"ML_INFERENCE_STARTED\"\n    ML_INFERENCE_COMPLETED = \"ML_INFERENCE_COMPLETED\"\n    ML_INFERENCE_FAILED = \"ML_INFERENCE_FAILED\"\n    ML_SIGNAL_FILTER_APPLIED = \"ML_SIGNAL_FILTER_APPLIED\"\n    ML_SIGNAL_REJECTED = \"ML_SIGNAL_REJECTED\"\n    ML_SIGNAL_SCORE_ADJUSTED = \"ML_SIGNAL_SCORE_ADJUSTED\"\n    ML_FEATURE_ALIGNMENT_FAILED = \"ML_FEATURE_ALIGNMENT_FAILED\"")
        with open(path, "w") as f:
            f.write(content)

path = "bist_signal_bot/notifications/formatter.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "def format_ml_inference_result" not in content:
        notif_str = """
def format_ml_inference_result(result) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_inference_text
    return f"<b>BIST Bot ML Filter Özeti</b>\\n\\n<pre>{format_ml_inference_text(result)}</pre>"

def format_ml_signal_filter_result(result) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_signal_filter_text
    return f"<b>BIST Bot ML Filter Özeti</b>\\n\\n<pre>{format_ml_signal_filter_text(result)}</pre>"

def format_ml_inference_batch_result(batch) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_batch_text
    return f"<b>BIST Bot ML Filter Özeti</b>\\n\\n<pre>{format_ml_batch_text(batch)}</pre>"
"""
        content = content + notif_str
        with open(path, "w") as f:
            f.write(content)

print("Updated audit and notifications")
