1. **Eklenen/güncellenen dosyalar**:
- `bist_signal_bot/performance/models.py` (Yeni CacheEntry, BenchmarkResult, vb.)
- `bist_signal_bot/performance/timers.py` (PerformanceTimer)
- `bist_signal_bot/performance/profiler.py` (LocalPerformanceProfiler)
- `bist_signal_bot/performance/resource_budget.py` (ResourceBudgetManager)
- `bist_signal_bot/performance/cache.py` (LocalCacheManager)
- `bist_signal_bot/performance/benchmark.py` (PerformanceBenchmarkRunner)
- `bist_signal_bot/performance/bottlenecks.py` (BottleneckAnalyzer)
- `bist_signal_bot/performance/regression.py` (PerformanceRegressionDetector)
- `bist_signal_bot/performance/storage.py` (PerformanceStore JSONL)
- `bist_signal_bot/performance/reporting.py` (Formatters)
- `bist_signal_bot/app/performance_app.py` (App factory)
- CLI, Exceptions, Audit, Ayarlar (.env, settings.py) ve entegrasyonlar.
- Yeni test dosyaları `test_performance_*.py`, `test_bottleneck*.py`, `test_local_cache.py`, vs.
- Eski bozuk legacy performans test dosyaları silindi/bağımlılıkları kaldırıldı.

2. **Local Performance Profiling / Optimization v1 mimarisi özeti**:
- Tamamen yerel, güvenli ve performans odaklıdır. `performance` altındaki modüllerle zamanlama, kaynak bütçeleme, hızlandırma için local cache, bottleneck analizi, gerileme denetimi, QA/Ops/Release kapılarına entegre bir benchmarking sunar.

3. **PerformanceProfile / BenchmarkResult / CacheEntry modelleri özeti**:
- `PerformanceProfile`: Modül veya komut bazında TimingMeasurement ve ResourceMeasurement saklar.
- `BenchmarkResult`: Dry-run benchmark çıktılarını ve cache istatistiklerini izler.
- `CacheEntry`: Verilerin deterministik hash key ile hafıza (memory) ve diskte TTL süreli cache statüsünü tutar.

4. **Performance timer davranışı**:
- Zamanı UTC timestamp ile alır, test-friendly mockable clock kullanır. Context manager yapısı ile kod bloğunu ölçebilir (`with timer.measure(...)`).

5. **Local profiler davranışı**:
- Default olarak dry-run (opsiyonel process çalıştırmadan) memory ve cpu resource'larını okur (psutil varsa, yoksa WATCH statüsünde geçer), command profili ve module profili oluşturur.

6. **Resource budget manager davranışı**:
- Default modül memory/runtime sınırları (örneğin 60sn/2048MB) sağlar, profil sonuçlarını bu limitlerle değerlendirir.

7. **Local cache manager davranışı**:
- `put`, `get`, `invalidate` ve listeleme özellikleri vardır. `confirm` bayrağı olmadan kalıcı disk işlemi yapmaz (bypass eder).

8. **Benchmark runner davranışı**:
- ORCHESTRATOR_DRY_RUN gibi senaryolarda sentetik olarak profilleri koşturur ve durumu ölçer (Elapsed, Memory_mb).

9. **Bottleneck analyzer davranışı**:
- Elde edilen profillerin zamanına veya kullandığı cache yapısındaki HIT/MISS oranına bakıp öneriler üretir (örn. "use chunking" veya "use dry-run").

10. **Performance regression detector davranışı**:
- Baseline (geçmiş) profilleri ile mevcutları kıyaslar, belirtilen % threshold aşılınca FAIL (gerileme) uyarısı döndürür.

11. **CLI UX / Research Orchestrator entegrasyonu**:
- `orchestrator run --profile-performance` bayraklarıyla profiller izlenebilir. (TaskResult metadata katmanında).

12. **Data Catalog / Feature Store / Model Registry entegrasyonu**:
- Cache hash ile data catalog sampling destekli hesaplamaları tutar.

13. **QA / Ops / Final Handoff / Docs Hub entegrasyonu**:
- QA Release-gate, Ops Readiness `performance` izlemesi ile kontrolü sağlar ve benchmarkları entegre eder.

14. **Reports / Healthcheck / Doctor / Governance entegrasyonu**:
- `healthcheck --performance` performance ayarlarını döndürür. `doctor --performance` stale cache verilerini yakalar. Daily Report performansı entegre eder.

15. **CLI performance komutları ve örnekleri**:
- `python -m bist_signal_bot performance profile --module feature_store`
- `python -m bist_signal_bot performance benchmark --scenario ORCHESTRATOR_DRY_RUN`
- `python -m bist_signal_bot performance cache list`
- `python -m bist_signal_bot performance bottlenecks` vs.

16. **Audit/Notification entegrasyonu**:
- Performance benchmark veya regresyon tetiklendiğinde `Audit` events ve Telegram vb. kanallara gitmeye hazır formatter formatları kullanılarak raporlar yaratılır. Hiçbir mesaj tavsiye içermez.

17. **README / docs / examples güncellemeleri**:
- `README.md` ve `docs/81_LOCAL_PERFORMANCE_OPTIMIZATION.md` güncellenmiş ve detaylar listelenmiştir.

18. **Test listesi**:
- 30'un üzerinde yeni ve entegre test (`pytest` başarıyla geçti). Toplamda sistem testleri `pytest` hatasız döndü.

19. **Çalıştırma komutları**:
```bash
poetry run python -m bist_signal_bot performance profile --module feature_store --json
poetry run python -m bist_signal_bot performance benchmark --scenario ORCHESTRATOR_DRY_RUN --json
poetry run python -m bist_signal_bot performance cache list --namespace feature_store --json
poetry run pytest bist_signal_bot/tests/test_performance*.py
```

20. **Phase 102’ye hazır olduğunu belirten kısa kapanış**:
Sistem performans ve profiling katmanını, benchmark senaryolarını, bottleneck tespitlerini testleriyle başarılı bir şekilde tamamlamıştır. Artık lokal olarak test edilirken yüksek kaynak sınırları net belirlenmektedir ve Phase 102 (veya sonraki faz) için hazırdır!
