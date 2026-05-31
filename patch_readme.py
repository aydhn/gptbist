import re

path = "README.md"
with open(path, "r") as f:
    content = f.read()

if "Model Registry" not in content:
    hook = """
## Phase 95: Local Model Registry & Governance (v1)
- Model Tracking: Tracks models, versions, artifacts, and experiments entirely offline.
- Governance Gates: Enforces model cards, validation metrics, and leakage checks before promotion to Active Research.
- Integrity: Ensures models are never used for real trade execution.
- Integrations: Fully integrated with ML inference, Strategy Registry, QA, and Ops layers.
"""
    # Assuming there's a features list
    if "## Core Features" in content:
        content = content.replace("## Core Features", hook + "\n## Core Features")
    else:
        content += "\n" + hook

with open(path, "w") as f:
    f.write(content)
