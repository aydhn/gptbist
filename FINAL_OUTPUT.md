## Phase 86: Unified Context Fusion V1 Completed

### 1. Eklenen/güncellenen dosyalar
- `bist_signal_bot/context_fusion/__init__.py`
- `bist_signal_bot/context_fusion/models.py`
- `bist_signal_bot/context_fusion/sources.py`
- `bist_signal_bot/context_fusion/collectors.py`
- `bist_signal_bot/context_fusion/normalization.py`
- `bist_signal_bot/context_fusion/weights.py`
- `bist_signal_bot/context_fusion/conflicts.py`
- `bist_signal_bot/context_fusion/evidence_gaps.py`
- `bist_signal_bot/context_fusion/research_graph.py`
- `bist_signal_bot/context_fusion/scoring.py`
- `bist_signal_bot/context_fusion/snapshot.py`
- `bist_signal_bot/context_fusion/engine.py`
- `bist_signal_bot/context_fusion/storage.py`
- `bist_signal_bot/context_fusion/reporting.py`
- `bist_signal_bot/app/context_fusion_app.py`
- `bist_signal_bot/cli/context_commands.py`
- CLI ana parsers, `core/exceptions.py`, `config/settings.py`, `core/audit.py`, `notifications/formatter.py` güncellendi.
- `.env.example`, `README.md` ve `docs/58_UNIFIED_CONTEXT_FUSION.md` eklendi/güncellendi.
- 20 yeni test dosyası (`bist_signal_bot/tests/test_context_*.py` vb.) eklendi.

### 2. Unified Context Fusion v1 mimarisi özeti
Sistem, birden fazla dağınık katmandan (Technical, ML, Ensemble, Risk, Execution, Calibration, Validation, Monte Carlo, Event Risk, Disclosure, Financials, Valuation, Factors, Breadth, Macro, Portfolio, Knowledge, Strategy Registry) gelen tüm araştırma sinyallerini tek bir local-first "Unified Context Snapshot" ve "Research Graph" altında birleştirir. Tüm işlemler offline ve research-only olarak kurgulanmıştır.

### 3. ContextSignal / UnifiedContextSnapshot / CompositeResearchScore modelleri özeti
Context status (STRONG_SUPPORT, PRESSURE, vb.), importance, direction enumları eklendi. Skorlar normalize edilip (0-100), composite score'lar evidence gap ve conflict penaltileri hesaba katılarak üretilir. Her modele mandatory disclaimer eklendi.

### 4. Context source registry ve collector davranışı
18 farklı katman desteklendi. Eksik store durumlarında warning + evidence gap üretiliyor. Herhangi bir cloud/broker bağımlılığı bulunmuyor.

### 5. Normalization ve weighting davranışı
Negatif etkiye sahip olan katmanlar (Risk, Macro, Event Risk) normalize edilirken skorları tersine çevrilir. Default ağırlıklar eksik katmanlara göre dinamik şekilde tekrar 1.0 üzerinden normalize edilir.

### 6. Conflict resolver davranışı
Technical Support vs Macro/Breadth/Risk/Event Risk gibi yaygın pazar çelişkilerini `high_score_high_risk`, `technical_vs_macro` gibi metotlar yardımıyla ContextConflict nesnelerine çevirir. Conflictler araştırma puanını (composite score) düşürür.

### 7. Evidence gap analyzer davranışı
İhtiyaç duyulan veya beklenen context layerlardan gelen verinin eski (stale), eksik veya hataya düşmesi durumlarında EvidenceGap üretilir. Critical veriler eksikse, conflict penalty uygular.

### 8. Research graph davranışı
Sembol, sinyal ve tüm context layer verilerini Node ve Edge (`PROVIDES_CONTEXT`, `TARGETS_SYMBOL`) şeklinde ilişkilendirir. Yerel bir graph snapshot JSONL olarak saklanır.

### 9. Composite scoring davranışı
Layer özetleri (base_score) hesaplanır. Conflict cezaları ve Evidence Gap cezaları (1-15 puan arası şiddetine göre) uygulanarak Final Adjusted Score ve ContextStatus belirlenir.

### 10-14. Entegrasyonlar
Scanner, Engine seviyesinde `--context-fusion` destekler. ML, Ensemble, Risk, Execution, Strategy Registry, Calibration, Validation, Monte Carlo, Events, Disclosures, Financials, Valuation, Factors, Breadth, Macro, Portfolio altyapılarına ContextCollector üzerinden entegre edildi. Healthcheck, CLI komutları, Audit ve Notification (mock/formatter) entegrasyonu tamamlandı.

### 15. CLI context komutları ve örnekleri
`python -m bist_signal_bot context build --symbol ASELS`
`python -m bist_signal_bot context show --symbol ASELS`
`python -m bist_signal_bot context graph --symbol ASELS`
`python -m bist_signal_bot context conflicts --latest`

### 16. Audit/Notification entegrasyonu
`UNIFIED_CONTEXT_SNAPSHOT_CREATED` ve `CONTEXT_FUSION_REPORT_CREATED` eventleri eklendi. Notification formatter tarafına uyarı formatter'ları eklendi.

### 17. Test listesi
Toplam 30 yeni unit ve entegrasyon test eklendi ve tümü `pytest` komutuyla başarıyla doğrulandı.

### 18. Çalıştırma komutları
`python -m bist_signal_bot context health` ve CLI test komutları hatasız çalıştı.

### 19. Kapanış
Phase 86 (Unified Context Fusion, Research Graph, Multi-layer Score Aggregation) v1 başarıyla tamamlandı. Sistem tam bir araştırma raporlama fabrikası seviyesine getirildi. Phase 87 için hazırdır.
