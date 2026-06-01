# Developer Guide
How to extend.

### Phase 99 Final Audit Subsystem

When submitting final code implementations, the developer must ensure they do not introduce terms related to live trading or financial guarantees. The `FinalSecurityAuditor` parses outputs to strictly reject and block release candidates carrying such assertions. Review `bist_signal_bot/final_audit/go_no_go.py` logic to understand how an MVP receives a GO or NO-GO decision prior to release packaging.
