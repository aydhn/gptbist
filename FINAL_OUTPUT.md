## Phase 47 Completed: Research Ledger, Experiment Tracking, Signal Journal, Attribution

1. **Eklenen/güncellenen dosyalar:**
   - `bist_signal_bot/research/__init__.py`
   - `bist_signal_bot/research/models.py`
   - `bist_signal_bot/research/ledger.py`
   - `bist_signal_bot/research/events.py`
   - `bist_signal_bot/research/lineage.py`
   - `bist_signal_bot/research/journal.py`
   - `bist_signal_bot/research/comparison.py`
   - `bist_signal_bot/research/attribution.py`
   - `bist_signal_bot/research/notes.py`
   - `bist_signal_bot/research/query.py`
   - `bist_signal_bot/research/reporting.py`
   - `bist_signal_bot/research/storage.py`
   - `bist_signal_bot/app/research_app.py`
   - `bist_signal_bot/cli/commands_research.py` (Argparse uyumlu)
   - Testler: `test_research_models.py`, `test_research_ledger.py`, `test_signal_journal.py`, `test_research_comparison.py`, `test_research_attribution.py`, `test_research_notes.py`, `test_research_query.py`, `test_research_lineage.py`
   - Modifiye Edilenler: `core/exceptions.py`, `config/settings.py`, `storage/paths.py`, `app/healthcheck.py`, `core/audit.py`, `notifications/formatter.py`, `cli/main.py`, `cli/parsers.py`, `README.md`, `.env.example`, `docs/30_DEVELOPER_GUIDE.md`

2. **Research Ledger v1 Mimarisi:**
   - Sistem append-only çalışır. Kayıtlar `research/ledger/` altında `.jsonl` dosyasına eklenir. `ResearchStore` bu veriyi yönetir ve hata toleranslı `_load_jsonl` ile okuma yapar.

3. **Modeller:**
   - `ResearchRun`: Backtest, ML, vs. işlemlerini sarmalar.
   - `SignalJournalEntry`: Scanner ve runtime kaynaklı sinyal logu.
   - `AttributionReport`, `ResearchComparisonReport`, `ResearchNote`: Raporlar ve manuel araştırma notları için veri sınıfları. Hepsi `Pydantic` kullanır.

4. **Event Builder:**
   - `ResearchEventBuilder`: Her engine'in ürettiği (Örn: `from_backtest_result`, `from_scan_report`) result objesini ortak bir `ResearchRun` verisine çevirir.

5. **Ledger ve Append-Only Storage:**
   - Edits (`status`, `tags`) overwrite yapmaz, ledger'ın sonuna metadata update gibi eklenir, yüklenirken conflict olursa son eklenen geçerli olur veya aggregation ile bulunur.

6. **Signal Journal ve Outcome:**
   - PENDING, POSITIVE, NEGATIVE outcome durumları kaydedilir. Update'ler `confirm=True` gerektirir ve uyarı dili/claims engellenir.

7. **Lineage:**
   - `ResearchLineageResolver`: Kayıtları ağaç yapısında parent-child mantığı ile (örneğin Backtest -> Optimizer) bağlar.

8. **Comparison ve Attribution:**
   - Sharpe, Win Rate, PnL gibi metriklerle stratejileri veya sembolleri kıyaslar. "Past performance is not indicative of future results" uyarısı rapora gömülüdür.

9. **Entegrasyonlar:**
   - Backtest, Scanner, Paper, ML, Runtime, Adaptive class'ları `.app.research_app` kullanılarak, çalıştıktan hemen sonra eğer `.env` dosyasında `RESEARCH_AUTO_LOG_...=True` ise ledger'a kayıt atar.

10. **CLI:**
    - `python -m bist_signal_bot research log --type MANUAL_NOTE --title "mock scan observation" --tag mock-test`
    - `python -m bist_signal_bot research list`
    - Argparse yapısında `commands_research.py` ve `parsers.py` entegre edilmiştir.

11. **Audit/Notification/Healthcheck:**
    - `get_full_health` içerisine `check_research` fonksiyonu eklendi. Dry-run storage instantiation test ediliyor. `audit.py`'da `RESEARCH_RUN_LOGGED` loglanıyor. Notification textleri hazır.

12. **Testler:**
    - Tüm alt modüller `tmp_path` kullanarak 0 internet ile deterministik şekilde Pytest üzerinden test edilmiştir.

13. **Çalıştırma Komutları:**
    - CLI test edildi. Argparse bağlamaları çözüldü. Ledger append test edildi. Bütün `research` alt komutları operasyonel.

14. **Kapanış:**
    - Phase 47 tamamlanmıştır. Sistem finansal regülasyonlar (no fake profit promises, no guaranteed claims) açısından tam güvenli (redacted), Offline çalışan, Append-only Ledger + Tracking + Attribution mimarisine kavuşmuştur. Sistem Phase 48'e hazırdır.
