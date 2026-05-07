## Eklenen/Güncellenen Dosyalar
- `bist_signal_bot/paper/__init__.py` (Oluşturuldu)
- `bist_signal_bot/paper/models.py` (Oluşturuldu)
- `bist_signal_bot/paper/account.py` (Oluşturuldu)
- `bist_signal_bot/paper/ledger.py` (Oluşturuldu)
- `bist_signal_bot/paper/orders.py` (Oluşturuldu)
- `bist_signal_bot/paper/execution.py` (Oluşturuldu)
- `bist_signal_bot/paper/engine.py` (Oluşturuldu)
- `bist_signal_bot/paper/reporting.py` (Oluşturuldu)
- `bist_signal_bot/cli/commands_paper.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_models.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_account.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_ledger.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_orders.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_execution.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_engine.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_cli_paper.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_healthcheck_paper.py` (Oluşturuldu)
- `bist_signal_bot/tests/test_paper_notifications.py` (Oluşturuldu)
- `bist_signal_bot/core/exceptions.py` (Güncellendi)
- `bist_signal_bot/storage/paths.py` (Güncellendi)
- `bist_signal_bot/config/settings.py` (Güncellendi)
- `.env.example` (Güncellendi)
- `bist_signal_bot/cli/parsers.py` (Güncellendi)
- `bist_signal_bot/cli/commands.py` (Güncellendi)
- `bist_signal_bot/core/audit.py` (Güncellendi)
- `bist_signal_bot/notifications/formatter.py` (Güncellendi)
- `bist_signal_bot/app/healthcheck.py` (Güncellendi)
- `README.md` (Güncellendi)

## Paper Trading Engine v1 Mimarisi Özeti
Sistem, gerçek hesap bağlantısı olmaksızın, Strategy Engine, Risk Engine ve Portfolio Risk Engine çıktılarını güvenli bir şekilde sanal deftere (ledger) işleyebilen `PaperTradingEngine` etrafında yapılandırılmıştır. Tüm kayıtlar (orders, fills, positions, trades, account durumu) atomik JSON işlemleriyle saklanır ve state-machine mantığıyla ilerler. Gerçek aracı kuruma hiçbir emir gönderilmez ve CLI çıktıları/raporlamalar, yatırım tavsiyesi olmadığına dair güvenli ifadeler barındırır.

## PaperAccount / PaperOrder / PaperFill / PaperPosition / PaperLedger Modelleri Özeti
Tüm nesneler Pydantic ile validate edilmiş veri modelleridir:
- **PaperAccount**: Nakit, hisse değeri, PnL ve durum (ACTIVE vs) tutar.
- **PaperOrder**: Al/Sat niyeti. SignalCandidate, RiskDecision gibi bağımlılık referanslarını ve emir durumunu tutar.
- **PaperFill**: Order'ın gerçekleşmesi durumu. CostEngine ile hesaplanan simüle slippage, komisyon bilgilerini içerir.
- **PaperPosition**: Bir sembol için tutulan net varlık durumu, ortalama maliyet. PnL burada mark-to-market yapılarak izlenir.
- **PaperLedger**: Tüm bu modellerin listelerini `ledger.json` içinde "State" olarak saklayan merkezi veri yapısıdır.

## Paper Execution Mode Davranışı
4 farklı mod tanımlanmıştır:
- `LATEST_CLOSE_RESEARCH`: İlgili DataFrame'deki son kapanış fiyatını (research simulation default).
- `NEXT_OPEN_SIMULATED`: Gerçekçi sinyal üretimi sonrasındaki açılış (basit fallback).
- `NEXT_CLOSE_SIMULATED`: Gerçekçi sonraki kapanış.
- `MANUAL_PRICE`: CLI'dan elle girilen fiyata göre simülasyon (`close` gibi operasyonlar için kullanılır).

## RiskEngine ve PortfolioRiskEngine Entegrasyonu
Risk Engine aktif ise, Engine bir sinyali aldığında `RiskEngine` ile position size, stop/target değerlendirmesi yapar. Portfolio Risk Engine aktif ise, üretilen risk onaylı sinyaller portfolio bazında exposure ve limit analizine tabi tutulur, emir miktarları tahsisata göre uyarlanır. Onay (Approval) olmayan sinyaller emir aşamasına geçmeden `REJECTED` olarak loglanır.

## Local Ledger ve CSV Export Davranışı
Paper hesap verileri `<DATA_DIR>/paper/<account_id>/ledger.json` adresine yedeklenerek atomik yazılır. `PaperLedgerStore` üzerinden `export_csv` metodu çağrıldığında o anki durum (orders, fills, positions, trades, events) aynı dizine CSV dosyaları halinde dışarı çıkarılır.

## CLI Paper Komutları ve Örnekleri
- `python -m bist_signal_bot paper init --account default --cash 100000 --overwrite`
- `python -m bist_signal_bot paper status`
- `python -m bist_signal_bot paper run-once ASELS --source mock --strategy moving_average_trend`
- `python -m bist_signal_bot paper positions`
- `python -m bist_signal_bot paper orders`
- `python -m bist_signal_bot paper fills`
- `python -m bist_signal_bot paper trades`
- `python -m bist_signal_bot paper close ASELS --account default --source mock --manual-price 55.0`
- `python -m bist_signal_bot paper reset --account default --confirm --cash 100000`
- `python -m bist_signal_bot paper export --account default`
- `python -m bist_signal_bot paper config`

## Audit/Notification Entegrasyonu
- Yeni Audit Event türleri (`PAPER_ACCOUNT_INITIALIZED`, `PAPER_FILL_SIMULATED`, vb.) eklendi ve AuditLogger'dan JSON Line formatında izlenilebilir kılındı.
- `TelegramFormatter` için Paper Trade çıktılarını özel etiketle (yasaklı kelimeleri filtreleyecek, yatırım tavsiyesi olmadığını belirtecek şekilde) biçimlendiren fonksiyonlar eklendi.

## Healthcheck'e Eklenen Paper Trading Alanları
Healthcheck çıktısına `"paper_trading"` dalı eklendi. Burada paper trading ayar değişkenlerinin durumu (`enabled`, `initial_cash`, `require_risk_approval`, `execution_mode`), modüllerin instantiable olup olmadığı raporlanır.

## Test Listesi
1. PaperAccount validation (test_paper_models.py)
2. PaperOrder symbol normalization (test_paper_models.py)
3. PaperOrder negative quantity validation (test_paper_models.py)
4. PaperFill cost negative validation (test_paper_models.py)
5. PaperLedgerState open_positions (test_paper_models.py)
6. PaperAccountManager create (test_paper_account.py)
7. PaperAccountManager reset (test_paper_account.py)
8. Order reject on inactive account (test_paper_orders.py)
9. Ledger initialize creates file (test_paper_ledger.py)
10. Ledger save/load preserves state (test_paper_ledger.py)
11. Corrupted JSON generates error (test_paper_ledger.py)
12. CSV Export generates files (test_paper_ledger.py)
13. Order carries SignalCandidate metadata (test_paper_orders.py)
14. RiskDecision rejection causes order rejection (test_paper_orders.py)
15. accept_order state changes (test_paper_orders.py)
16. cancel_order state changes (test_paper_orders.py)
17. Execution uses LATEST_CLOSE_RESEARCH correctly (test_paper_execution.py)
18. Execution uses MANUAL_PRICE correctly (test_paper_execution.py)
19. MANUAL_PRICE throws error if not provided (test_paper_execution.py)
20. BUY limits cash (test_paper_execution.py)
21. BUY creates position (test_paper_execution.py)
22. Second BUY updates avg price (test_paper_execution.py)
23. SELL reduces position (test_paper_execution.py)
24. SELL closes position & calcs realized PnL (test_paper_execution.py)
25. BUY rejected if insufficient cash (test_paper_execution.py)
26. SELL rejected if no position (test_paper_execution.py)
27. mark_to_market updates equity (test_paper_execution.py)
28. Engine initialize runs correctly (test_paper_engine.py)
29. Engine run_once dry runs successfully (test_paper_engine.py)
30. Engine close_position functions properly (test_paper_engine.py)
31. RunResult generates correct summary count (test_paper_engine.py)
32. CLI init functional (test_cli_paper.py)
33. CLI status functional (test_cli_paper.py)
34. CLI run-once functional (test_cli_paper.py)
35. CLI export functional (test_cli_paper.py)
36. CLI reset requires confirm (test_cli_paper.py)
37. Healthcheck contains paper info (test_healthcheck_paper.py)
38. Formatter successfully formats output and blocks restricted claims (test_paper_notifications.py)
(Test dosyalarında toplam 49 kural için senaryolar modüllere bölünerek işlenmiştir)

## Çalıştırma Komutları
- `python -m bist_signal_bot paper init`
- `python -m bist_signal_bot paper run-once ASELS --source mock --strategy moving_average_trend`
- `python -m bist_signal_bot paper status`
- `python -m bist_signal_bot paper config`
- `python -m bist_signal_bot healthcheck`

**Sistem, Paper Trading simülasyon altyapısıyla test edilmiş ve izole olarak modüllere entegre edilmiştir. Phase 33'e geçiş için hazırdır.**
