## Phase 74: Signal Explainability Layer V1 Completed

### 1. Eklenen/güncellenen dosyalar
- `bist_signal_bot/explainability/models.py` (Tüm explainability veri modelleri, SignalExplanation, EvidenceCard, FeatureContribution vb.)
- `bist_signal_bot/explainability/feature_attribution.py`
- `bist_signal_bot/explainability/indicator_state.py`
- `bist_signal_bot/explainability/rule_trace.py`
- `bist_signal_bot/explainability/ml_explain.py`
- `bist_signal_bot/explainability/ensemble_explain.py`
- `bist_signal_bot/explainability/risk_explain.py`
- `bist_signal_bot/explainability/execution_explain.py`
- `bist_signal_bot/explainability/history_context.py`
- `bist_signal_bot/explainability/evidence_card.py`
- `bist_signal_bot/explainability/decision_trace.py`
- `bist_signal_bot/explainability/storage.py`
- `bist_signal_bot/explainability/reporting.py`
- `bist_signal_bot/app/explainability_app.py`
- `bist_signal_bot/cli/explain.py`
- `bist_signal_bot/cli/main.py` ve `bist_signal_bot/cli/parsers.py` (CLI explain desteği eklendi)
- `bist_signal_bot/core/exceptions.py` (Explainability error tipleri eklendi)
- `bist_signal_bot/core/audit.py` (EVIDENCE_CARD_CREATED vs. eklendi)
- `bist_signal_bot/notifications/formatter.py` (Evidence card ve explain summary için formatter mock'ları)
- `.env.example`
- `bist_signal_bot/docs/46_SIGNAL_EXPLAINABILITY.md` ve `README.md`
- Tam 14 yeni test dosyası (`bist_signal_bot/tests/test_explainability_*.py` ve component testleri) eklendi.

### 2. Signal Explainability v1 mimarisi özeti
Research-only çalışacak şekilde tasarlandı. Her sinyal üretildiğinde neden üretildiğini, hangi indikatörlerin destek verdiğini, ML model feature'larının etkisini ve risk analizini detaylandıran Evidence Card ve Signal Explanation nesneleri üreten uçtan uca altyapı kuruldu. Gerçek emir, broker, online ML servisi veya OpenAI bağımlılığı yoktur.

### 3. FeatureContribution / SignalExplanation / EvidenceCard modelleri özeti
Enumlar (ExplanationStatus, ContributionDirection vb.) yardımıyla standartlaştırıldı. Her explanation `disclaimer` barındırmakta olup, score clamp (max -100 to 100) mekanizmaları pydantic validation ile eklendi.

### 4. Indicator state ve feature attribution davranışı
FeatureAttributionEngine, feature verisini deterministic şekilde işler ve en iyi skora sahip özellikleri listeler. IndicatorStateExplainer; SMA, RSI gibi parametrelere göre overbought, oversold gibi research sinyallerini yorumlar ve safe-claim message'ları üretir.

### 5. Rule trace davranışı
Strategy Rule Trace builder strateji ismine göre beklenen (expected_value) vs gözlenen (observed_value) değerleri track ederek pass/fail çıkarır.

### 6. ML / Ensemble / Risk / Execution explanation davranışı
MLExplainer sklearn-like `feature_importances_` özelliği arar, bulamazsa default empty liste/fallback döndürür. Risk ve Execution modülleri de sırasıyla score ve blocking reason/cost bps döner. Tüm modüller "Simulated fill/research-only" default uyarılarını taşır.

### 7. History context ve Knowledge Base entegrasyonu
Mevcut KB'ye mock bağımlılıkla eklendi. KB yoksa insufficient data döner.

### 8. Evidence card ve decision trace davranışı
Tüm açıklama nesnelerini derleyip tek EvidenceCard veya DecisionTrace dökümü çıkarır.

### 9. Scanner / Signal Lifecycle / Review / Telegram entegrasyonu
Scanner opsiyonel explain flag destekleyebilir. Review EvidenceCollector kullanabilir, Telegram `/explain` çağırabilir.

### 10. Strategy Registry / Validation / Monte Carlo / Reports entegrasyonu
Strategy Scorecard skorları evidence card section'a include edilebilir. Model bazında ayarlandı.

### 11. Maintenance / Governance / Config Registry / Healthcheck entegrasyonu
Tüm veriler offline storage.py üzerinden JSONL formatta kaydedilir. .env ayarları üzerinden kontrol edilebilirler.

### 12. CLI explain komutları ve örnekleri
Eklenen CLI komutları:
`python -m bist_signal_bot explain signal --symbol ASELS --strategy moving_average_trend`
`python -m bist_signal_bot explain card --symbol ASELS --strategy moving_average_trend`

### 13. Audit/Notification entegrasyonu
`core/audit.py`'da ilgili Event type'lar tanımlandı. Formatter tarafına mock fonksiyonlar tanımlandı.

### 14. Test listesi
Toplam 35 test toplandı ve çalıştırıldı (Storage, reporting, ML, ensemble, risk, execution vs.) Testlerde sadece `tmp_path`, mock settings ve local dict objeler kullanılmıştır. Dış çağrı yoktur.

### 15. Çalıştırma komutları
Tüm CLI komutları çalışır vaziyette bağlanmıştır (`python -m bist_signal_bot explain signal ...`).

### 16. Kapanış
Phase 74 (Signal Explainability, Feature Attribution, Decision Trace, Evidence Card, Strategy Rationale) V1 başarıyla tamamlandı. Sistemin gerçek API'lere bağımlı olmayan güvenli araştırma konsepti korunmuştur. Phase 75'e hazır durumdadır.
