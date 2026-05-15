with open("bist_signal_bot/app/healthcheck.py", "r") as f:
    content = f.read()

# I used Mock import earlier but then I overwrote it. Let's fix healthcheck again.
if "from bist_signal_bot.app.quality_app import" in content:
    pass

# We should make sure run_healthcheck isn't broken
if "def run_healthcheck(" not in content:
    content += "\n\ndef run_healthcheck(settings=None):\n    hc = AppHealthcheck(settings=settings)\n    return hc.run()\n"

with open("bist_signal_bot/app/healthcheck.py", "w") as f:
    f.write(content)
