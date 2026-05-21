
## Research Lab Integration (Phase 59)
The Orchestrator can now conditionally trigger the `run_research_lab_plan` configuration. This capability delegates complex insights (e.g. adaptive or drift reports) to generate a Research Lab batch plan instead of stalling the runtime pipeline. Note that this integration strictly *generates the plan*, but execution must be started separately via the queue manager to protect runtime performance.
