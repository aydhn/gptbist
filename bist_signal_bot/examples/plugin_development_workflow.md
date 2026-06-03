# Plugin Development Workflow

1. List available contracts:
`python -m bist_signal_bot plugins contracts`

2. Discover plugins:
`python -m bist_signal_bot plugins discover --dir examples/plugins`

3. Validate:
`python -m bist_signal_bot plugins validate --plugin example_strategy_plugin`

4. Test (dry-run):
`python -m bist_signal_bot plugins test --plugin example_strategy_plugin --dry-run`

5. Load metadata:
`python -m bist_signal_bot plugins load --plugin example_strategy_plugin --metadata-only`

6. Governance:
`python -m bist_signal_bot plugins governance --plugin example_strategy_plugin`
