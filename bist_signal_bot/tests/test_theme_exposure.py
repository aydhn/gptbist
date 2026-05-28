
from bist_signal_bot.factors.theme import ThemeExposureEngine
from bist_signal_bot.factors.models import ThemeDefinition
def test_theme_exposure():
    t = ThemeExposureEngine()
    themes = t.load_theme_definitions()
    assert len(themes) == 1

    td = ThemeDefinition(theme_id="1", name="X", description="X")
    saved = t.save_theme_definition(td, confirm=False)
    assert "Theme not saved, confirmation required" in saved.warnings
