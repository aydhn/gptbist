def is_safe_claim(text: str) -> bool:
    unsafe_keywords = ["trade ready", "işlem yapılabilir", "kesin", "al/sat", "hedef fiyat", "garanti"]
    for kw in unsafe_keywords:
        if kw in text.lower():
            return False
    return True
