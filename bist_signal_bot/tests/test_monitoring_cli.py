from bist_signal_bot.cli_monitoring import run_monitoring_cli

def test_cli_status(capsys):
    run_monitoring_cli("status")
    captured = capsys.readouterr()
    assert "Monitoring OK" in captured.out

def test_cli_run(capsys):
    run_monitoring_cli("run", object_type="STRATEGY", object_id="moving_average_trend", save=False)
    captured = capsys.readouterr()
    assert "Snapshot created" in captured.out

def test_cli_alerts(capsys):
    run_monitoring_cli("alerts", unacknowledged=True)
    captured = capsys.readouterr()
    assert "Loaded 0 alerts." in captured.out

def test_cli_report(capsys):
    run_monitoring_cli("report")
    captured = capsys.readouterr()
    assert "Monitoring report generated." in captured.out
