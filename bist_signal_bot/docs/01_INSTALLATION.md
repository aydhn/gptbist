# Installation Guide

## Requirements
- Python >= 3.10

## Steps
1. Create a virtual environment.
2. Install packages (`requirements.txt`).
3. Generate `.env` from template using `deploy env-template`.
4. Initialize directories using `deploy init-dirs`.
5. Select a safe profile like `RESEARCH_ONLY`.

## Troubleshooting
If you encounter errors:
- Run `python -m bist_signal_bot deploy doctor --deep`
- Check folder permissions.
