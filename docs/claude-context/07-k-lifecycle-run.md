# K-A: Drift-tetiklemeli challenger + haftalik yeniden egitim dongusu - gercek uctan uca kosu

Tarih: 2026-10-10. Yalniz arastirma/paper. Gercek emir yok ("No real order sent."). `promote(confirm=True)` HIC cagrilmadi.

## Izolasyon
- Gercek forward champion registry'sine DOKUNULMADI. Ayri dizin: `data/k_lifecycle_run/` (model_registry, models, logs, security/kill switch, run1.log).
- Trial ledger: gercek `trials.sqlite` kopyalandi (`trials_copy.sqlite`; DSR deneme sayisi korunsun diye bos ledger kullanilmadi). Gercek ledger degismedi.
- Calistirma betigi: scratchpad `k_run.py` (DailyModelTrainer + ModelLifecycle + DailyDriftMonitor; `model-loop evaluate` CLI'si yalniz 1h/intraday, gunluk yol CLI'ye bagli degil - bu bir bosluk).

## Calistirilan
Gercek yerel gunluk arsiv: 629 sembol, 2537 seans, son seans 2026-10-09. Aile `ml_xs_hgb`, h=5, `{max_depth:3, retrain_every:60}`, top_n=8 (portfolios.json watch portfoyu ile ayni parametreler).

1. `due_for_retrain` (bos registry) -> due=True ("no daily model registered").
2. Baseline egitim as_of=2026-08-28 (ctx.index[-31]) -> kayit. Sure: ~16 dk (955 sn). Sonuc: gate verdict **REJECTED** (failed: `pbo`), registry durumu **WATCH**, champion DEGIL.
3. `due_for_retrain` (bugun) -> True (42 gun eski >= 7).
4. Drift: `lifecycle.evaluate(2026-10-09)` (referans = son 60 seansdan onceki 250 seans, guncel = son 60 seans; PSI/KS + skor dagilimi). Zorlama (force) GEREKMEDI, drift dogal olarak tetiklendi: `feature_drift: 7/30 features PSI>=0.25`, severity=alert, retrain=True.
   - alert: beta_120 (PSI 0.84, KS 0.27), idio_vol_60 (0.35), res_xu_20 (0.94), res_xu_60 (1.01), mkt_breadth_long (12.5), mkt_ret_20_pct (1.77), usdtry_trend_20_pct (8.3).
   - Model skoru: PSI 0.0046, KS 0.0109, p=0.19 -> skor dagilimi sabit.
   - Diger ozellikler PSI < 0.01 (rank-normalize oldugu icin beklenen).
5. Challenger egitimi as_of=2026-10-09: ~14 dk. Verdict **REJECTED** (pbo), status **FAILED_VALIDATION**, tag `challenger`. Karsilastirma: `gate_verdict=REJECTED: not eligible for promotion`; `promotion_recommended=False`.
6. `promote(challenger, confirm=False)` -> **BLOCKED**: `gate_verdict=REJECTED (CANDIDATE required)` + `preflight failed: Security Preflight Failed: Found 8 secret leaks in configuration`. Champion: None (hicbir zaman champion olmadi).
Toplam sure: 29 dk 43 sn (cogu 2 x gate/ledger kosusu: `run_family_daily`).

## Bulgular
- Hat teknik olarak uctan uca calisiyor: egit -> kaydet -> drift -> challenger -> karsilastirma -> promote reddi -> WATCH / FAILED_VALIDATION.
- **Duzeltilen hata**: `ctx_as_of` tz-aware (UTC) as_of alinca `np.datetime64` UserWarning veriyordu (lifecycle `_to_dt` UTC-aware gecer). Artik tz'si kaldirilip normalize ediliyor (`model_loop/daily_lifecycle.py`). Test eklendi.
- **Basarisiz / tasarim sinirlamasi (DUZELTILMEDI, gate gevsetilmedi)**: `DailyModelTrainer.train` gate'e tek konfigurasyonluk grid (`{k:[v]}`) verir; `CandidateGate` PBO'yu >=2 konfigurasyon ister, aksi halde NaN -> `pbo` kriteri basarisiz. Sonuc: bu yoldan egitilen bir model HICBIR ZAMAN CANDIDATE olamaz (her zaman WATCH/FAILED_VALIDATION). Guvenli yonde (fail-closed) ama "challenger -> promote" yolu fiilen olu. Karar gerekir: komsu grid ile (ornegin max_depth +-1) PBO hesaplanir ama ledger deneme sayisi artar. Ayrica portfolios.json'daki `v2_verdict=CANDIDATE` ile bu kosunun REJECTED cikmasi ayni gate'in farkli (tam-grid) girdisinden kaynaklanir; bu nedenle bu kosu o portfoyun CANDIDATE'ligini dogrulamaz.
- **Drift yorumu (basarisiz/zayif sinyal)**: alert veren ozelliklerin cogu piyasa-duzeyi (tum sembollerde ayni deger) ozelliklerdir (mkt_*, usdtry_*, res_xu_*) -> 60 seanslik pencerede yalniz 60 bagimsiz gozlem var, satir basina kopyalanmis olduklari icin KS p-degerleri sahte-tekrar nedeniyle anlamsiz derecede kucuk. Drift gercek bir rejim degisimi OLABILIR ama istatistiksel kaniti zayif; tetikleyici bu haliyle asiri hassas. Duzeltilmedi (esik/tasarim karari).
- Preflight `Found 8 secret leaks in configuration` hatasi lokal ortamda (.env) var; promote'u engeller (istenen fail-closed davranis). Calistirilmadi/arastirilmadi.
- Haftalik yeniden egitim: `due_for_retrain(registry, today, 7)` calisti; zamanlayici/otomatik cagri bu kosuda test edilmedi (runtime'a bagli degil, `daily-train --only-if-due` CLI'si mevcut).

## Testler
- `bist_signal_bot/tests/test_model_loop_lifecycle.py`: yeni - non-CANDIDATE (WATCH/INSUFFICIENT_DATA/REJECTED/""/"candidate") challenger, champion'lu ve champion'suz, preflight+kill switch tamken bile `confirm=True` ile BLOCKED; preflight/kill switch/confirm tek tek zorunlu; ctx_as_of tz testi. dosya 23 test geciyor (onceden 15); test_daily_ml.py ile birlikte 43 gecti (ctx_as_of testinden once).
