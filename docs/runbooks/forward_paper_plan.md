# Forward Shadow Paper Plan (pre-registered)

Bu proje arastirma ve paper simulation amaclidir. Yatirim tavsiyesi degildir. Gercek emir gondermez. (No real order sent.)

## Neden
Backtest sonuclari survivorship yanlili (evren = halen listeli hisseler) ve cok kez test edilmis (global N ~254, DSR ~ 0).
Tek durust test ileriye donuk (live out-of-sample) kanittir. Portfoyler yalnizca SIMULE edilir; hicbir emir gonderilmez.

## Neden ileriye donuk test gercek testtir
Forward testte evren **o gun** gorulen evrendir: delisted/survivorship yanlilgi YOKTUR (arastirma evreni halen listeli
hisselerdir, bu yanli). Karar o gun kapanisinda, yalnizca o gune kadarki veriyle verilir; sonuc sonradan degistirilemez
(hash zinciri). Bu yuzden backtest "aday"ligi yalnizca izleme hakki verir, kanit forward'dan gelir.

## Baslangic
- Baslangic tarihi = ilk `python -m bist_signal_bot forward run-daily` kosusunun as_of tarihi (decisions.jsonl header
  `planned_start_date` + ilk karar). Portfoyler `data/forward/portfolios.json` (v1) icinde DONDURULUR (icerik hash'li, versioned).
  Yeni surum yalnizca acik komutla: `forward freeze --force-new-version` -> `portfolios.v2.json` (onceki hash'e bagli, eskisi
  degismez, zincirlere `freeze` kaydi dusulur). Sessizce yeniden secilmez.
- Secim (v2 istatistigi, `<aile>_daily_xs_ew2`, gercekci dolum + dayaniklilik kriterleri): aile ve ufuk (5, 10) basina ledger'daki en yuksek
  net excess Sharpe'li deneme. **Tier**: `candidate` = en yeni v2 `daily_all_*.json` raporunda CANDIDATE + robust (raporun
  secilen parametreleri kullanilir); `watch` = CANDIDATE etiketli ama denetimde dusurulmus (`FORWARD_TIER_OVERRIDES`,
  su an `ml_xs_hgb|5`: etiket batch-sirasi artefakti, global havuz n=26->310, global_dsr 0.17); `control` = en iyi
  `FORWARD_N_CONTROLS` kural/ML ailesi + her ufuk icin tohumlu rastgele-skor **placebo** (gurultu kalibrasyonu; hash-tohumlu,
  donmus dosyada). Bilinmeyen verdict -> control. Benchmarklar: EW evren, XU100, nakit.
- Planlanan minimum gozlem penceresi: **3 ay (90 takvim gunu) ve >= 60 canli islem gunu**. Bundan once karar YOK (INSUFFICIENT).

## Karar kurali (veri gorulmeden yazildi; header'a da yazilir)
Yalniz **candidate** tier portfoylerine PASS/FAIL verilir (watch/control bilgi amaclidir, `forward report` bunlari
WATCH/CONTROL diye etiketler ve `informational_verdict` gosterir). Placeholder-komisyon senaryosunda PASS icin hepsi:
1. EW-evren benchmark'a gore kumulatif excess > 0 (ve EW'yi >= 60 canli gun sonra yenmeli).
2. Nakde gore NAV alfasi > 0.
3. Gunluk excess ortalamasinin Newey-West (overlap-duyarli, lag >= ufuk) t-istatistigi >= max(2.0, z(1-0.05/K)), K = candidate tier sayisi.
4. >= 6 kapanmis sepet ve sepet-bazli EW'ye karsi isabet orani >= %50.
5. Maks. drawdown < %20.
6. Ayni ufuktaki **placebo** shadow'u yenmek: placebo'ya gore kumulatif excess > 0 ve gunluk fark NW t >= 2.
**Genel basari** = >= 1 candidate PASS **ve** placebo'da edge yok (placebo NW t(excess vs EW) < 2). Placebo edge gosterirse
sonuc `INCONCLUSIVE_PLACEBO_EDGE` (cerceve gurultu uretiyor demektir); candidate yoksa `NO_CANDIDATE`.
**Asla yeniden ayar (retune) yapilmaz**; parametre/aile/tier degisikligi = yeni forward dizini veya acik yeni freeze surumu + yeni plan.
PASS bile tek basina canli islem izni degildir; yalnizca "aday olarak izlemeye devam" anlamina gelir.

## Isleyis
- Gunluk is: `forward run-daily` (veri yenile -> freshness gate -> sonuclari isle -> karar yaz -> NAV). Idempotent.
- Karar kapanista (as_of close) verilir, giris ertesi acilis, cikis as_of+ufuk kapanis; DailyCostModel iki senaryo, nakit faizi, 100.000 TL tam lot NAV.
- **v2 dolum semantigi** (arastirmayla ayni `DailyContext.semantics`): dolamayan giris (hacim 0, limit-up acilis, H==L kilit) alinmaz,
  slot nakitte kalir; kilitli limit-down cikis ilk kilitsiz kapanisa ertelenir (sepet cikis kaydi tum hisseler satilinca yazilir);
  maliyetler fiyat-limit bayragiyla hesaplanir.
- **ML**: `data/forward/models/<aile>__<anahtar>/` altinda blok basina (model + kalibrator) joblib + state.json
  (FEATURES_VERSION / ozellik-sema hash'i; uyusmazlikta kullanilmaz). Is yalnizca vadesi gelen blogu (retrain_every) yalnizca gecmis veriyle
  egitir, aksi halde cache'ten yukleyip bugunun kesitini skorlar; gecmis gun skorlari yeniden hesaplanmaz. Ilk gun tum bloklar
  egitilir (bootstrap, dakikalar-onlarca dakika). Modeller shadow-only: champion degil, `tier` state'e ve karar kaydina yazilir.
  Esdegerlik testi: `tests/test_forward_v2.py` (cache == tam walk-forward).
- Benchmarklar: EW evren, XU100, nakit. Rapor: `forward report` (tier, v2 verdict, placebo karsilastirmasi, OVERALL); saglik: `forward health`.
- Alarmlar (data/forward/alerts.jsonl): bayat veri, is hatasi, hash zinciri kirigi, NAV drawdown %10/15/20, kill switch degisimi.

## Komutlar
```
python -m bist_signal_bot forward freeze                       # portfolios.json (bir kez)
python -m bist_signal_bot forward freeze --force-new-version   # portfolios.v2.json (acik, eskisi degismez)
python -m bist_signal_bot forward run-daily                    # gunluk is (log: timings_s)
python -m bist_signal_bot forward report                       # istatistik + tier + verdict + OVERALL
python -m bist_signal_bot forward health --dry-run             # saglik raporu + Telegram metni (gondermez)
```
