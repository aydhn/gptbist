from bist_signal_bot.disclosures.normalizer import DisclosureNormalizer
def test_normalize_text():
    norm = DisclosureNormalizer()
    res = norm.normalize_text("This   is a    test. \n\n With  spaces.")
    assert res == "This is a test. With spaces."
