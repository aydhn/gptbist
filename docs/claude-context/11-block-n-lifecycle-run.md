# Blok N — Öğrenme döngüsü (2026-10-10)

Yalnız paper/simülasyon. No real order sent.

## Yapılanlar
- **Komşu grid (N1):** `DailyModelTrainer.neighbor_grid` (logit C×{0.5,1,2}; hgb max_depth±1, alt sınır 2; meta K×{2/3,1,1.5}).
  Birincil = MERKEZ (`fixed_primary`, sonradan en iyi komşuya kaymaz). Ledger'a `grid_tag=neighbor_grid`; N şişmesi kabul edildi ve dürüst yazılır.
  CandidateGate eşikleri DEĞİŞMEDİ.
- **Drift (N2):** `DailyDriftMonitor` artık tarih başına 1 gözlem (etkin örneklem=gün), özellik başına KS p-değerleri Benjamini-Hochberg, "anlamlı"=BH p<alpha VE PSI>=warn,
  retrain = (anlamlı/testable >= 0.2 VE n_sig>=2) VEYA skor kayması. `DAILY_DRIFT_LEGACY=True` eski davranış. Çıplak `DriftMonitor` (intraday) eski davranışta kaldı.
- **Lifecycle CLI (N3):** `model-loop daily-cycle [--only-if-due] [--dry-run] [--confirm]` (ELLE; zamanlayıcı yok). Gate CANDIDATE değilse yalnız rapor; promote yalnız `--confirm` +
  `ModelLifecycle.promote` koşulları (gate CANDIDATE, better-than-champion, kill-switch, preflight, audit). `rollback` artık kill-switch aktifken bloklanır.
- **CPCV çapraz doğrulama (N5):** bkz. `10-cpcv-crosscheck.md` (skfolio 1.8.0, BSD-3; `cv.py` doğru; bağımlılık repoya EKLENMEDİ).

## Gerçek veri koşusu (hgb, ufuk 5, as_of 2026-10-09)
- challenger `mloop_daily_hgb_h5_20261009_045617cd`: **gate_verdict=REJECTED** (yalnız `pbo` kriteri düştü), durum FAILED_VALIDATION, champion olmadı.
- OOS net Sharpe 2.48 (excess vs EW 2.44), DSR 0.999, **PBO 0.514** (eşik 0.25), n_trials_ledger=8, n_grid_trials=2 (max_depth 2 merkez, alt sınır nedeniyle komşu yalnız 3).
- Yorum: yüksek Sharpe, survivorship/zaman-doğru olmayan evren ve birincil seçim şişmesi nedeniyle iyimser kabul edilir; PBO>0.5 seçimin OOS'ta medyanın altına düşme olasılığının yüksek olduğunu gösterir.
  Daily lifecycle artık PBO'yu HESAPLAYABİLİYOR (NaN değil) ve gate doğru karar veriyor: aday değil.
- İlk koşuda drift girdisi yoktu (kayıtlı champion yok), "forced" gerekçesi.

## Bilinen sınırlar
- HGB'de max_depth merkez 2 iken komşu sayısı 2 (alt sınır); daha zengin komşuluk için ikinci eksen (ör. learning_rate) eklenebilir (ama N artar).
- Kesit özelliklerinin günlük ortalaması yapısal olarak sabit; drift fiilen piyasa-düzeyi özelliklerde ve skorda görünür.
- Ledger trial_id'si as_of içermez: aynı konfigürasyonların yeni veriyle yeniden eğitimi N'ye eklenmez (önceden de böyleydi).
- CLI gerçek arşivle yalnız bir kez koşuldu; haftalık düzen ELLE (`--only-if-due`).
