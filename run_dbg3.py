from bist_signal_bot.data_import.normalization import ImportNormalizer
normalizer = ImportNormalizer()
print(normalizer.normalize_numeric("1.234,56"))
