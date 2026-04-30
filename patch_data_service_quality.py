import sys

def modify_tests():
    # The duplicate index was getting cleaned by the new DataCleaner before the QualityChecker saw it!
    # Let's disable the data cleaner explicitly in this test so the quality checker can catch it.
    with open("bist_signal_bot/tests/test_data_service_quality.py", "r") as f:
        content = f.read()

    new_service = """    service = MarketDataService(
        provider=bad_provider,
        quality_checker=checker,
        validate_quality=True,
        fail_on_quality_error=True,
        clean_data=False # DISABLE CLEANER SO ERROR REACHES QUALITY CHECKER
    )"""

    old_service = """    service = MarketDataService(
        provider=bad_provider,
        quality_checker=checker,
        validate_quality=True,
        fail_on_quality_error=True
    )"""

    content = content.replace(old_service, new_service)

    with open("bist_signal_bot/tests/test_data_service_quality.py", "w") as f:
        f.write(content)

modify_tests()
