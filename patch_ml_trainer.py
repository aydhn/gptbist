import re

path = "bist_signal_bot/ml/training/trainer.py"
with open(path, "r") as f:
    content = f.read()

# Add to trainer to log experiments and artifacts using ModelRegistryApp factory
if "create_experiment_tracker" not in content:
    imports = """from bist_signal_bot.app.model_registry_app import create_experiment_tracker, create_model_artifact_manager
from bist_signal_bot.model_registry.models import ModelKind, ModelArtifactFormat
"""
    content = content.replace("from bist_signal_bot.ml.training.splits import MLTimeSeriesSplitter", imports + "from bist_signal_bot.ml.training.splits import MLTimeSeriesSplitter")

if "exp_tracker.start_run" not in content:
    # Hook into train method
    hook_start = """
            # Experiment Tracking Start
            exp_tracker = None
            run_id = None
            if getattr(self.settings, "ENABLE_MODEL_REGISTRY", False):
                try:
                    exp_tracker = create_experiment_tracker(self.settings)
                    run = exp_tracker.start_run(
                        experiment_name=config.model_type,
                        model_name=config.model_type,
                        model_kind=ModelKind.CLASSIFIER if config.task_type.value == "CLASSIFICATION" else ModelKind.REGRESSOR,
                        parameters=config.model_dump() if hasattr(config, "model_dump") else config.dict(),
                    )
                    run_id = run.run_id
                except Exception as e:
                    self.logger.warning(f"Failed to start experiment run: {e}")
    """

    # Need to find start of train method body, after try:
    train_try_idx = content.find("        try:\n            train_input.validate_input()")
    if train_try_idx != -1:
        insert_idx = train_try_idx + 13
        content = content[:insert_idx] + hook_start + content[insert_idx:]

if "exp_tracker.complete_run" not in content:
    hook_end = """
            # Experiment Tracking Complete
            if exp_tracker and run_id:
                try:
                    metrics = res.classification_metrics.model_dump() if res.classification_metrics else res.regression_metrics.model_dump() if res.regression_metrics else {}
                    exp_tracker.complete_run(run_id, metrics)
                except Exception as e:
                    self.logger.warning(f"Failed to complete experiment run: {e}")

            # Artifact Registration
            if getattr(self.settings, "ENABLE_MODEL_REGISTRY", False) and config.save_model and hasattr(res, "artifact") and res.artifact.model_path:
                try:
                    art_mgr = create_model_artifact_manager(self.settings)
                    from pathlib import Path
                    art_mgr.register_artifact(
                        path=Path(res.artifact.model_path),
                        model_id=res.artifact.model_id,
                        artifact_format=ModelArtifactFormat.PICKLE, # Assuming pickle for now
                        confirm=True
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to register model artifact: {e}")
    """

    audit_idx = content.find("            from bist_signal_bot.core.audit import AuditLogger")
    if audit_idx != -1:
        content = content[:audit_idx] + hook_end + "\n" + content[audit_idx:]

with open(path, "w") as f:
    f.write(content)
