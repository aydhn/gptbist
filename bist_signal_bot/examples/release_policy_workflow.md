# Release Policy Workflow Example

1. `python -m bist_signal_bot release-policy status`
2. `python -m bist_signal_bot release-policy change --title "Add X" --type FEATURE --modules x`
3. `python -m bist_signal_bot release-policy compatibility`
4. `python -m bist_signal_bot release-policy freeze --branch release/v1.0.0 --target-version 1.0.0 --confirm`
