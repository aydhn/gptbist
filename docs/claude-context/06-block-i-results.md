# Blok I — farklı edge arayışı: sonuçlar (2026-10-10)

Aynı CandidateGate (eşikler DEĞİŞMEDİ) + v2 dayanıklılık katmanı + deterministik global-çoklu-test DSR
(ledger anlık görüntüsü sabit, batch sırasından bağımsız). Evren: 629 hisse × 10 yıl günlük, top-8, ufuk 3/5/10/15,
iki komisyon senaryosu (sıfır + yer tutucu) birlikte. Her deneme ledger'da; `_daily_xs_ew2` havuzunda şimdi **450 deneme**
(placebo hariç; ledger toplamı 1266).

**İYİMSERLİK SINIRI:** Delist olmuş semboller ücretsiz yfinance verisinde yok; tüm sonuçlar survivorship nedeniyle iyimser,
gerçek değer raporlanandan düşüktür, sınır ölçülemez.

## Denenen aileler (yeni, `families_daily_i.py`)
`xs_lowvol_x_momentum`, `xs_multi_horizon_ensemble`, `xs_regime_momentum`, `xs_sector_rs_liquid`,
`xs_turnover_damped_momentum` (ızgaralar ≤4 kombinasyon). Likit evren koşusunda (`--min-adv 5e7`) ayrıca
`xs_momentum_12_1` ve `xs_rel_strength_sector`. Raporlar: `daily_all_20261010T104633.json` (tüm evren),
`daily_all_20261010T105449.json` (ADV≥5e7).

## Sonuç: BAŞARISIZ — edge bulunamadı
- Her iki koşuda tüm hücreler (aileler × 4 ufuk × 2 senaryo) **REJECTED**, `robust=N`. Tüm placebo'lar da REJECTED.
- En iyi görünen hücreler (hepsi REJECTED, `trim_top_events` ve `drop_top_symbols` dayanıklılık testlerinde kalıyor):
  - `xs_lowvol_x_momentum` h=15, ADV≥5e7: nominal CAGR %42.8, maxDD -%39.7, nakde karşı alfa +%5.9, EW'ye karşı excess CAGR +%12.6.
  - `xs_rel_strength_sector` h=10, ADV≥5e7: nominal CAGR %46.7, maxDD -%64.2, excess CAGR +%19.0; `drop_top_symbols` geçti ama
    `trim_top_events`, `year_stability`, `event_cap` kaldı.
- Rejim koşullu momentum ve devir sönümlü momentum EW evrenin altında (excess negatif). Çok-ufuk topluluk ve likit sektör RS
  yalnız uzun ufuklarda küçük pozitif excess verdi, dayanıklılığı geçemedi.
- Likit evren (ADV≥5e7) sinyalin kalitesini artırmadı; kenar zaten kuyruk olaylara ve birkaç sembole dayanıyor.

## Testlenmeyenler ve nedenleri
- **Kalite/değer (F/K, P/D):** ücretsiz zaman-doğru (point-in-time) temel veri yok; mevcut yfinance temel verisi bakış-ileri
  yanlılığı taşır. Kullanılmadı. `xs_quality_proxy` yalnız fiyat tabanlı vekildir.
- **Meta-labeling (d):** kuralı gereği yalnız dayanıklı bir birincil sinyalde denenir; dayanıklı birincil sinyal olmadığı için YAPILMADI.
- **Açılış→kapanış giriş zamanlaması (c):** günlük çubuklarla bağımsız bir giriş-zamanlama ailesi test edilemez (intraday arşiv kısa);
  yalnız t+1 kapanış gecikme duyarlılığı (`entry_delay.py`) raporlanır. Gerçek zamanlama kanıtı forward dolum verisinden gelecek.
- Sektör: yerel sektör verisi yok; "sektör" RS veri güdümlü korelasyon kümeleriyle yaklaştırıldı.

## Ölçülmüş en iyi reel CAGR
Değişmedi: ≈ %27.7 (overlay ile ≈ %24.7, maxDD -%18; survivorship ve TÜFE-2025-04 sınırlarıyla iyimser). Hedef %75 **ULAŞILAMADI**.
