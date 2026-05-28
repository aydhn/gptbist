
# Phase 83: Factor Exposure & Sector Rotation V1

Bu modül, BIST hisseleri için deterministik faktör skorlaması, sektör rotasyonu ve tema pozisyonu hesaplar.

## Kurallar
- HTML Scraping yasaktır.
- Gerçek emir gönderimi yapılmaz.
- OpenAI/LLM kullanılmaz.
- Tüm çıktılar "Research-Only" disclaimer içerir.

## Mimari
- **Factor Input Builder**: Adjusted OHLCV, financial quality, valuation metriklerini offline birleştirir.
- **Factor Scorer**: Cross-sectional Z-score ve percentile hesaplar.
- **Exposure Engine**: Sembol, strateji veya portföy seviyesinde maruz kalınan faktörleri çıkartır.
- **Crowding Analyzer**: Tek faktöre aşırı yığılmaları tespit eder.

## CLI
```bash
python -m bist_signal_bot factors compute ASELS
python -m bist_signal_bot factors exposure --symbol ASELS
python -m bist_signal_bot factors sector-rotation
```
