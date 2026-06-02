import os
from pathlib import Path

# docs/83_ADVANCED_REPORT_TEMPLATES.md
p1 = Path("bist_signal_bot/docs/83_ADVANCED_REPORT_TEMPLATES.md")
p1.write_text('''# Advanced Report Templates

## Mimari
- Template kinds
- Section library
- Composer flow
- Narrative safety
- Export pack
- Manifest
- Validation
- Existing reports integration
- QA/Ops integration
- Güvenli dil kuralları
- Troubleshooting
''')

# examples/report_templates_workflow.md
p2 = Path("bist_signal_bot/examples/report_templates_workflow.md")
p2.write_text('''# Report Templates Workflow
- list
- show
- sections
- compose
- validate
- export dry-run
- export confirm
- manifest
- report
''')

print("Phase 103 Part 10 edits applied.")
