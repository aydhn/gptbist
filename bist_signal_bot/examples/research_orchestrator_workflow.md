# Research Orchestrator Workflow

### 1. View Campaigns
```bash
python -m bist_signal_bot orchestrator campaigns
```

### 2. Plan a Run
```bash
python -m bist_signal_bot orchestrator plan --campaign QUICK_RESEARCH_SCAN --symbols ASELS THYAO
```

### 3. View the DAG
```bash
python -m bist_signal_bot orchestrator dag --campaign FULL_RESEARCH_PIPELINE --mermaid
```

### 4. Execute a Run Safely (Dry-Run)
```bash
python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --symbols ASELS THYAO --dry-run
```

### 5. Check Guardrails
```bash
python -m bist_signal_bot orchestrator guardrails --campaign QUICK_RESEARCH_SCAN
```

### 6. View Results
```bash
python -m bist_signal_bot orchestrator report
```

### Disclaimer
*These workflows are meant strictly for local research and offline automation. They do not execute real market trades.*
