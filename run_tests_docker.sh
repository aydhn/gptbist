#!/bin/bash
export PYTHONPATH=.
python -m pytest bist_signal_bot/tests/test_research_lab_*.py bist_signal_bot/tests/test_cli_research_lab.py bist_signal_bot/tests/test_healthcheck_research_lab.py
