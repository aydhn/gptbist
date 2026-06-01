# Final Handoff Workflow Example

This example demonstrates how to generate and view the Final MVP Handoff artifacts.

**Note:** This command execution strictly produces software artifacts and research metadata. No actual trading execution takes place.

### 1. Build the Handoff Manifest

```bash
python -m bist_signal_bot final-handoff build --save
```

*Expected Result:* Scans module states, orchestrates builders, and saves a `final_handoff_manifest.jsonl` entry.

### 2. Generate the Release Pack

```bash
python -m bist_signal_bot final-handoff release-pack --save --json
```

*Expected Result:* Aggregates documentation, examples, and existing manifests, checks their SHA256 hashes, and outputs the release pack JSON.

### 3. Generate the Operator Playbook

```bash
python -m bist_signal_bot final-handoff operator-playbook
```

*Expected Result:* Prints the generated Markdown playbook containing daily, weekly, and emergency routines.

### 4. Generate the Final Report

```bash
python -m bist_signal_bot final-handoff report --latest
```

*Expected Result:* Reads the latest saved manifest and release pack, then prints the overarching Handoff Report.
