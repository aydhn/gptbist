from bist_signal_bot.app.healthcheck import healthcheck_factors
def test_healthcheck():
    assert healthcheck_factors()['factors_enabled']
