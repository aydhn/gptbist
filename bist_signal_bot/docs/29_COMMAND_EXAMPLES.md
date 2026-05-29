# Command Examples

## Analyst Review Workflow

Create a new case:
```bash
python -m bist_signal_bot review-workflow create --symbol ASELS
python -m bist_signal_bot review-workflow create --symbol ASELS --strategy moving_average_trend --save
```

List open cases:
```bash
python -m bist_signal_bot review-workflow list
python -m bist_signal_bot review-workflow list --status OPEN
```

Show a case and its checklist:
```bash
python -m bist_signal_bot review-workflow show CASE_ID
python -m bist_signal_bot review-workflow checklist CASE_ID
```

Manage Decision Journal and Disposition:
```bash
python -m bist_signal_bot review-workflow journal CASE_ID --add-note "Context reviewed; macro pressure remains active." --actor analyst
python -m bist_signal_bot review-workflow disposition CASE_ID --set RESEARCH_WATCH --note "Conflicts remain unresolved."
```

Sign-offs and Data Actions:
```bash
python -m bist_signal_bot review-workflow signoff CASE_ID --request --reason "Critical context conflict"
python -m bist_signal_bot review-workflow signoff SIGNOFF_ID --approve --actor lead_analyst
python -m bist_signal_bot review-workflow data-actions --resolve ACTION_ID --note "Financials imported"
```

Reporting and Patterns:
```bash
python -m bist_signal_bot review-workflow patterns
python -m bist_signal_bot review-workflow report
```

Full pipeline examples with `context build` and `scan symbols`:
```bash
python -m bist_signal_bot context build --symbol ASELS --save --create-review-case
python -m bist_signal_bot scan symbols ASELS THYAO --source local_file --strategy moving_average_trend --context-fusion --review-workflow
```
