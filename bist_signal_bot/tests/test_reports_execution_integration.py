import pytest
from bist_signal_bot.reports.sections import execution_sim_section

def test_reports_markdown_disclaimer_execution_sim():
    txt = execution_sim_section({})
    assert "Execution Simulation" in txt
    assert "No real orders sent." in txt
