# Leaderboard Workflow Examples

1. List available cohorts:
`python -m bist_signal_bot leaderboard cohorts`

2. Build a leaderboard:
`python -m bist_signal_bot leaderboard build --type STRATEGY_COHORT --save`

3. Rank a specific candidate:
`python -m bist_signal_bot leaderboard rank --candidate-type STRATEGY --candidate-id my_strategy`

4. Compare candidates:
`python -m bist_signal_bot leaderboard compare --type STRATEGY --a strat1 --b strat2`

5. View policies:
`python -m bist_signal_bot leaderboard policies`

6. Select candidates based on policy:
`python -m bist_signal_bot leaderboard select --latest --policy strategy_research_selection_v1`

7. Generate report:
`python -m bist_signal_bot leaderboard report --latest`
