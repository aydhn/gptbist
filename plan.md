1. **Update `core/exceptions.py`**: Add the requested exceptions (`ModelRegistryError`, `ModelExperimentError`, `ModelArtifactError`, etc.).
2. **Update `model_registry/models.py`**: Create the requested enums (`ModelRegistryStatus`, `ModelKind`, `ModelArtifactFormat`, `ExperimentStatus`, `ModelGovernanceStatus`, `ModelPromotionStage`, `ModelDriftType`) and Pydantic/dataclass models (`ModelRecord`, `ExperimentRun`, `ModelArtifact`, `ModelCard`, `ModelValidationSummary`, `ModelCalibrationSummary`, `ModelPromotionRequest`, `ModelDriftFinding`, `ModelLineageEdge`, `ModelGovernanceAssessment`, `ModelRegistryReport`). Ensure proper disclaimers and validation logic are included.
3. **Update `model_registry/registry.py`**: Create `LocalModelRegistry` with methods like `register_model`, `list_models`, `get_model`, `update_model_status`, `archive_model`, `validate_model_record`, `safe_model_summary`.
4. **Update `model_registry/experiments.py`**: Create `ExperimentTracker` with methods `start_run`, `complete_run`, `fail_run`, `list_runs`, `best_run`, `validate_run`.
5. **Update `model_registry/artifacts.py`**: Create `ModelArtifactManager` with methods `register_artifact`, `checksum`, `infer_format`, `validate_artifact`, `check_loadable`, `artifact_for_model`.
6. **Update `model_registry/model_cards.py`**: Create `ModelCardBuilder` with methods `build_card`, `default_intended_use`, `default_not_intended_use`, `known_limitations`, `risk_notes`, `validate_card`, `render_markdown`.
7. **Update `model_registry/validation.py`**: Create `ModelValidationGovernance` with methods `summarize_validation`, `status_from_metrics`, `check_min_sample`, `check_overfit`, `check_feature_quality`, `validate_summary`.
8. **Update `model_registry/calibration.py`**: Create `ModelCalibrationGovernance` with methods `summarize_calibration`, `status_from_calibration`, `check_reliability`, `check_sample_count`, `validate_summary`.
9. **Update `model_registry/promotion.py`**: Create `ModelPromotionManager` with methods `request_promotion`, `evaluate_promotion`, `approve_research_promotion`, `reject_promotion`, `promotion_history`.
10. **Update `model_registry/drift.py`**: Create `ModelDriftDetector` with methods `detect_prediction_drift`, `detect_performance_decay`, `detect_calibration_decay`, `detect_feature_drift_linked`, `drift_score`, `classify_drift`.
11. **Update `model_registry/lineage.py`**: Create `ModelLineageTracker` with methods `add_edge`, `model_lineage`, `build_lineage_graph`, `link_dataset_to_experiment`, `link_feature_set_to_model`, `link_model_to_signal_or_strategy`.
12. **Update `model_registry/governance.py`**: Create `ModelGovernanceEngine` with methods `assess_model`, `artifact_status`, `model_card_status`, `validation_status`, `calibration_status`, `feature_quality_status`, `leakage_status`, `blocking_reasons`, `final_status`.
13. **Update `model_registry/storage.py` and `storage/paths.py`**: Create `ModelRegistryStore` and add `get_model_registry_dir` in `paths.py`. Implement JSONL file paths and methods like `append_model`, `load_models`, `save_report`, etc.
14. **Update `model_registry/reporting.py`**: Implement dict formatters (`model_record_to_dict`, etc.), dataframe converters (`models_to_dataframe`), and markdown text formatters.
15. **Update `app/model_registry_app.py`**: Create factory functions (`create_model_registry_store`, `create_local_model_registry`, etc.).
16. **Integrations**:
    - `ml/inference/engine.py` / `ml/training/trainer.py`: Modify inference to accept `model-registry` metadata and `model-id`. Update training engine to log runs in experiment tracker and artifacts.
    - `feature_store/leakage.py` / `data_catalog/lineage.py`: Ensure integrations work.
    - `strategy_registry/evidence.py`, `strategy_registry/scorecard.py`, `context_fusion/collectors.py`, `review_workflow/case_builder.py`, `qa/release_gate.py`, `ops/store_checks.py`, `ops/staleness.py`, `ops/readiness.py`, `reports/collector.py`, `reports/sections.py`, `maintenance/doctor.py`, `app/healthcheck.py`: Update tools to include model registry checks.
17. **Update `config/settings.py`**: Add `ENABLE_MODEL_REGISTRY`, `MODEL_REGISTRY_DIR_NAME`, validation limits, drift warnings, promotion blockers, etc.
18. **Update CLI**: Update `cli/commands.py` / `cli/parsers.py` to add `model-registry` with `list`, `show`, `register`, `experiments`, `artifact`, `card`, `validate`, `calibration`, `governance`, `promote`, `drift`, `lineage`, `report`, `recent`, `config`.
19. **Update Core/Security**: `core/audit.py`, `notifications/formatter.py`, `config_registry/schema.py`.
20. **Tests**: Implement 60+ tests specified. Check that they don't break existing tests, run deterministic and purely locally.
21. **Documentation**: Update `README.md`, `docs/71_MODEL_REGISTRY_AND_MODEL_GOVERNANCE.md`, `examples/model_registry_workflow.md`.
22. **Pre-commit**: Complete pre-commit steps and ensure tests pass.
