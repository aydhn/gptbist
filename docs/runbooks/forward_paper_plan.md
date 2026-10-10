# Forward Shadow Paper Plan (pre-registered)

Bu proje arastirma ve paper simulation amaclidir. Yatirim tavsiyesi degildir. Gercek emir gondermez. (No real order sent.)

## Neden
Backtest sonuclari survivorship yanlili (evren = halen listeli hisseler) ve cok kez test edilmis (global N ~254, DSR ~ 0).
Tek durust test ileriye donuk (live out-of-sample) kanittir. Portfoyler yalnizca SIMULE edilir; hicbir emir gonderilmez.

## Baslangic
- Baslangic tarihi = ilk `python -m bist_signal_bot forward run-daily` kosusunun as_of tarihi (decisions.jsonl header
  `planned_start_date` + ilk karar). Portfoyler `data/forward/portfolios.json` icinde DONDURULUR (icerik hash'li, versioned);
  secim kurali: aile basina ve ufuk (5, 10) basina ledger'daki en yuksek net excess Sharpe'li deneme. Sessizce yeniden secilmez.
- Planlanan minimum gozlem penceresi: **3 ay (90 takvim gunu) ve >= 60 canli islem gunu**. Bundan once karar YOK (INSUFFICIENT).

## Karar kurali (veri gorulmeden yazildi; header'a da yazilir)
Placeholder-komisyon senaryosunda bir portfoy PASS olur ancak hepsi saglanirsa:
1. EW-evren benchmark'a gore kumulatif excess > 0.
2. Nakde gore NAV alfasi > 0.
3. Gunluk excess ortalamasinin Newey-West (overlap-duyarli, lag >= ufuk) t-istatistigi >= max(2.0, z(1-0.05/K)), K = dondurulmus portfoy sayisi (Bonferroni).
4. >= 6 kapanmis sepet ve sepet-bazli EW'ye karsi isabet orani >= %50.
5. Maks. drawdown < %20.
Aksi halde FAIL. **Asla yeniden ayar (retune) yapilmaz**; parametre/aile degisikligi = yeni forward dizini + yeni plan.
PASS bile tek basina canli islem izni degildir; yalnizca "aday olarak izlemeye devam" anlamina gelir.

## Isleyis
- Gunluk is: `forward run-daily` (veri yenile -> freshness gate -> sonuclari isle -> karar yaz -> NAV). Idempotent.
- Karar kapanista (as_of close) verilir, giris ertesi acilis, cikis as_of+ufuk kapanis; DailyCostModel iki senaryo, nakit faizi, 100.000 TL tam lot NAV.
- Benchmarklar: EW evren, XU100, nakit. Rapor: `forward report`; saglik: `forward health`.
- Alarmlar (data/forward/alerts.jsonl): bayat veri, is hatasi, hash zinciri kirigi, NAV drawdown %10/15/20, kill switch degisimi.

## Komutlar
```
python -m bist_signal_bot forward freeze          # portfolios.json (bir kez)
python -m bist_signal_bot forward run-daily       # gunluk is
python -m bist_signal_bot forward report          # istatistik + verdict
python -m bist_signal_bot forward health --dry-run  # saglik raporu + Telegram metni (gondermez)
```
