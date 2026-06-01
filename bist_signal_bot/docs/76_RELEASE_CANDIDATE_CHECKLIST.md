# Release Candidate Checklist

This checklist documents the required items for reaching a successful MVP freeze (Phase 99) towards Handoff (Phase 100).

## 1. Required Commands
- [x] `healthcheck`
- [x] `doctor`
- [x] `qa release-gate`
- [x] `ops readiness`
- [x] `bootstrap release-bundle`
- [x] `reports daily`
- [x] `final-audit run`
- [x] `final-audit candidate build`
- [x] `final-audit go-no-go`

## 2. Check Validations
The `GoNoGoEvaluator` enforces the following minimum standards:
- **BLOCKED**: If `FinalSecurityAuditResult` flags any broker or unsafe claim terms ("trade ready").
- **FAIL**: If `FinalAcceptanceSuite` or `FinalIntegrationMatrix` reports any failures.
- **PASS**: All checks imported safely and simulated test passes without unexpected warnings.

## 3. Security Requirements
- [x] No broker calls
- [x] No cloud LLMs (OpenAI, Anthropic etc.) during standard run mode
- [x] No HTML scraping
- [x] No explicit financial advice or exact profit guarantees.

## 4. Documentation Validation
Ensure the MVP docs hub holds:
- README.md updated with Phase 99.
- 75_FINAL_PRE_RELEASE_AUDIT.md
- 76_RELEASE_CANDIDATE_CHECKLIST.md
- examples/final_audit_workflow.md

## 5. Next Steps
Once Go decision evaluates successfully, prepare for Phase 100 (Final Handoff), finalizing the code archive, building standalone CLI releases, and issuing the repository handover.
