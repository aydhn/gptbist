# Data Catalog Workflow Example

This example demonstrates how to register, profile, and assess a dataset using the CLI.

```bash
# 1. See all available contracts
python -m bist_signal_bot data-catalog contracts

# 2. Register a new CSV file (Dry run first)
python -m bist_signal_bot data-catalog register --path data/imports/my_financials.csv --kind FINANCIALS --dry-run

# 3. Register it for real
python -m bist_signal_bot data-catalog register --path data/imports/my_financials.csv --kind FINANCIALS --confirm

# 4. Profile the newly created dataset
# (Replace DATASET_ID with the one printed in the previous step)
python -m bist_signal_bot data-catalog profile DATASET_ID --save

# 5. Assess the quality against the contract
python -m bist_signal_bot data-catalog quality DATASET_ID

# 6. Check for schema drift
python -m bist_signal_bot data-catalog drift DATASET_ID

# 7. Check the overall data quality gate
python -m bist_signal_bot data-catalog gate --dataset-id DATASET_ID
```

All interactions use local files and operate offline.
