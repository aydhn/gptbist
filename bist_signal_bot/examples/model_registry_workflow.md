# Model Registry Workflow

This document provides examples for using the model registry via CLI.

## 1. Register a new model
```bash
python -m bist_signal_bot model-registry register --name baseline_rf --kind CLASSIFIER --version 1.0 --confirm
```

## 2. Track an experiment
*(Usually done programmatically during training, but you can view them)*
```bash
python -m bist_signal_bot model-registry experiments list
```

## 3. Register an artifact
```bash
python -m bist_signal_bot model-registry artifact register --path data/models/rf_v1.json --model-id <MODEL_ID> --confirm
```

## 4. Build a Model Card
```bash
python -m bist_signal_bot model-registry card build <MODEL_ID>
```

## 5. Review Governance
```bash
python -m bist_signal_bot model-registry governance <MODEL_ID>
```

## 6. Promote to Active Research
```bash
python -m bist_signal_bot model-registry promote <MODEL_ID> --stage ACTIVE_RESEARCH --reason "Passed validation" --confirm
```

## 7. Generate a Report
```bash
python -m bist_signal_bot model-registry report
```
