# Local Model Registry & Governance (v1)

The Local Model Registry operates strictly as an offline metadata tracking system for ML models.

## Key Design Principles
1. **Research-Only:** The registry does not facilitate live deployment or order execution. Models are for research and candidate signaling.
2. **Local-First:** All metadata (experiments, model cards, lineage, drift) is stored in local JSONL files. No cloud services (e.g. MLflow) are used.
3. **Strict Governance:** Models must pass validation, calibration, and feature leakage checks before they can be promoted to `ACTIVE_RESEARCH`. Missing model cards or corrupted artifacts block promotion.

## Components
- **ModelRecords & Artifacts:** Tracks the file paths, checksums, and formats of local models (e.g., Pickle, Joblib, ONNX).
- **ExperimentTracker:** Records run parameters, metrics, and configurations used during ML training.
- **ModelCardBuilder:** Generates Markdown documentation regarding the model's intended use, features, and limitations.
- **GovernanceEngine:** Aggregates checks (leakage, artifacts, cards, validation) to produce a `ModelGovernanceAssessment`.
- **DriftDetector:** Monitors prediction distribution and performance decay over time.

## Integration
- **ML Inference:** The inference engine checks the registry governance status before generating predictions. If blocked, inference fails gracefully.
- **QA & Ops:** Automated gates verify the registry's health, ensuring necessary directories and active models exist.
