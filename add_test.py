def add_test_zero_equity():
    with open('bist_signal_bot/tests/test_portfolio_exposure.py', 'a') as f:
        f.write("\n\ndef test_exposure_analyzer_calculate_zero_equity():\n")
        f.write("    import datetime\n")
        f.write("    state = PortfolioState.model_construct(\n")
        f.write("        equity=0.0,\n")
        f.write("        cash=0.0,\n")
        f.write("        holdings=[],\n")
        f.write("        timestamp=datetime.datetime.now(datetime.UTC),\n")
        f.write("        daily_signal_count=0\n")
        f.write("    )\n")
        f.write("    analyzer = ExposureAnalyzer()\n")
        f.write("    report = analyzer.calculate_exposure(state)\n")
        f.write("    assert report.gross_exposure_pct == 0.0\n")
        f.write("    assert report.cash_pct == 1.0\n")
        f.write("    assert \"Portfolio equity is zero or negative\" in report.issues\n")

add_test_zero_equity()
