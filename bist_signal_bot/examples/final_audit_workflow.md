# Example Workflow: Executing a Final Audit

This document explains how to perform a final audit dry-run against the BIST Signal Bot to verify MVP candidate status.

## Step 1: Run Acceptance Suite
```bash
python -m bist_signal_bot final-audit acceptance --json
```

## Step 2: Validate Output Contracts
```bash
python -m bist_signal_bot final-audit contracts
```

## Step 3: Integration Matrix Check
```bash
python -m bist_signal_bot final-audit integration
```

## Step 4: Evaluate Security Audit
Ensures no active network broker calls exist and language remains "safe".
```bash
python -m bist_signal_bot final-audit security
```

## Step 5: Build Candidate and Go/No-Go Decision
Build the candidate and verify standard release checks against the latest logs.
```bash
python -m bist_signal_bot final-audit candidate build --save
python -m bist_signal_bot final-audit go-no-go
```

## Step 6: Generate Formal Report
```bash
python -m bist_signal_bot final-audit report
```

Check the `./data/final_audit/reports/` folder for `final_audit_report.md` output which documents the formal QA validations.
