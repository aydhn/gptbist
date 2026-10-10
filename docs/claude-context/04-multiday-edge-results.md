# Çok günlü ufuk — ölçülmüş sonuçlar (2026-10-10)

Veri: 629 hisse + XU100 + USDTRY, 10 yıl günlük (yfinance, düzeltilmiş), evren = **halen listeli** semboller
(**survivorship yanlılığı: sonuçlar iyimser**). Long-only, top-8, 100.000 TL, ufuklar 3/5/10/15 işlem günü,
aynı CandidateGate (eşikler gevşetilmedi), her deneme ledger'da. Nominal TL getiriler (CPI verisi yok; nakit %37 politika faizi proxy).

## Koşu 1 — mutlak getiri modu (YÖNTEM HATASI bulundu)
Gate mutlak net getiriyi sıfırla kıyasladığı için enflasyonlu TL piyasasında rastgele long-only seçim bile pozitifti:
`cal_turn_of_month` **placebo'su CANDIDATE** çıktı. Mutlak-mod CANDIDATE sonuçları (xs_quality_proxy, xs_rel_strength_sector, ...)
kanıt sayılmaz. Ledger aileleri `*_daily` (silinmez, N'ye sayılır).

## Koşu 2 — excess modu (aday olmak için EW-evrene karşı fazla getiri + nakde karşı pozitif alfa)
Ledger aileleri `*_daily_xs_ew`. Tüm placebo'lar REJECTED. 14 aile x 4 ufuk (67 koşu):
- Tek CANDIDATE hücre: `xs_rel_strength_sector` h=10 (placeholder komisyonda); h=5 yalnız komisyon-sıfırda, h=3 ve h=15 REJECTED.
  Net NAV Sharpe 1.67, nominal CAGR %85, EW-evrene fazla CAGR ~%48, **maxDD -%65** (kullanıcı sınırı %20'nin çok üstünde).
  En iyi %10 ex-post kazanan çıkarılınca fazla CAGR'ın ~%59'u kalıyor (survivorship duyarlılığı).
- Diğer ailelerde excess pozitif ama gate'i geçmeyen: xs_quality_proxy (excess CAGR ~%22-43, DSR yetersiz), xs_rel_strength_index, xs_momentum (5-15g).
  Ters dönüş, hacim şoku, düşük oynaklık/beta, 12-1 momentum, FX duyarlılığı, takvim aileleri: edge yok (excess negatif).
- Çoklu test: aile içi N ile DSR sınırda (0.93-0.95); **aileler arası global N (254) ile DSR ≈ 0** (`edge_validation/global_multiplicity.py`).
  14 aile taranırken tek bir aday şans beklentisiyle uyumlu. Sonuç: **sağlam edge kanıtı yok**; sector adayı "zayıf/şüpheli".

## Dürüst sonuç
Rule-based çok günlü ailelerde, excess-over-EW + global çoklu test altında, kullanıcı DD sınırını (%20) karşılayan ve
%75 reel CAGR hedefine yaklaşan sağlam aday bulunamadı. Not: nominal CAGR %85 görünse de bu nominal TL, survivorship'li,
DD -%65 ve çoklu test düzeltmesinden sonra anlamsız.

## Koşu 3 — v2 (gerçekçi dolum + dayanıklılık katmanı) — 2026-10-10
Çerçeve sertleştirildi (gate eşikleri DEĞİŞMEDİ, yalnız ek katmanlar): tarih-bağımlı fiyat limitleri (±%20 → ±%10,
geçiş tarihi 2020-03-01 DOĞRULANMADI), tavan açılışta dolmayan girişler nakde döner, kilitli limit çıkışı ertelenir,
bar sağlığı filtresi, ADV'ye bağlı spread proxy. Dayanıklılık: en iyi %5 olay kırpma, en iyi 10 sembol çıkarma, takvim yılı
kararlılığı, maliyet x2, olay tavanı +%20, global-çoklu-test DSR (MAD-kırpılmış varyans, N asla kırpılmaz). Ledger: `*_daily_xs_ew2`.
Rapor: `data/edge_validation/reports/daily_all_20261010T073518.json` (h=3,5,10,15; top-8; EW'ye karşı excess; iki komisyon senaryosu).
- Tüm kural-tabanlı aileler REJECTED (robust=N); tüm placebo'lar REJECTED.
- ML: yalnız `ml_xs_hgb` h=5 CANDIDATE+robust (NAV Sharpe 3.77, nominal CAGR %224, maxDD -%33, excess CAGR ~%168, 4 deneme).
  `ml_xs_hgb` h=3/10/15, `ml_xs_logit`, `ml_xs_meta` REDDEDİLDİ (trim_top_events ve/veya global_dsr).
- Yorum (şüpheci): önceki adli denetimde ML "edge"i tek faktöre (aşırı kısa vadeli momentum / tavan devamı) ve 2024-26
  piyango olaylarına indirgenmişti; survivorship, kapasite, VBTS/tek-fiyat mekanikleri modellenmedi. Bu aday yalnız
  PAPER/forward-test adayıdır; kanıt değil. Ayrıntılı v2 denetimi ayrı ajan tarafından yürütülüyor (aşağıya eklenecek).

### ml_xs_hgb h=5 — v2 denetimi (derinlemesine, 2026-10-10)
Parametreler: depth=3, R=60, h=5, embargo=2, stride=5, top-8. Sayılar yeniden üretildi (1955 olay, NAV Sharpe 3.77, excess CAGR %168).
- **Karar artefakt:** aynı deneme bugünkü ledger ile yeniden koşunca `robust:global_dsr` düşüyor (resmî koşuda havuz n=26, DSR 0.9997;
  bugün n=310, DSR 0.17). CANDIDATE etiketi batch sırasına bağlıydı → **geçerli aday sayılmaz**, yalnız WATCH/forward izleme adayı.
- Sızıntı yok (truncation farkı 0, zaman sıralı early-stopping/kalibratör). Küçük kusur: purge nominal t1 kullanıyor (ertelenen çıkış; 44/1.46M satır, ihmal edilebilir; düzeltilecek).
- Dolum: slotların %2.4'ü nakde kaldı; tavana 1 tick yakın dolum %0.15. Maliyet x3 / +50bps altında kenar sürüyor.
- Gecikme: t+1 kapanış girişte kenar 197→109 bps (SR 2.58→1.34); kenarın büyük kısmı giriş günü açılış→kapanış hareketi.
- Yoğunlaşma: en iyi %5 olay excess'in %79'u; ilk 10 sembol %33.6. Tavan-kuyruğu filtresi kenarı bozmuyor (eski logit "piyango" faktörü yok).
- Likidite: ADV≥5e7 → excess CAGR %92 (trim5 ~0); ADV≥1e8 → %50 (trim5 negatif). Pratik kapasite ~1e6 TL.
- Zaman ters holdout 2017-20: ort. 31 bps, SR 0.52 (zayıf); 2021-23: 175 bps; 2024-26: 214 bps.
- Survivorship: ≥3 yıldır listeli → excess CAGR %58; eski-hayatta-kalan (377 sembol) ile yeniden eğitimde ≈ %0.9 (kenarın neredeyse tamamı yeni listelenenlerde).
- Atıf: volume_shock (düşük) × ret_60/mom_120 etkileşimi ("sessiz momentum"); tek özellik baseline'ları edge'i yeniden üretmiyor.
- Forward geçersiz kılma eşikleri: ~300 seans sonra olay başı net excess <40 bps veya en iyi %5 çıkınca ≤0; NAV excess Sharpe <0.75 / excess CAGR <%20 (12 ay);
  120 seansta kümülatif excess <0 ve maxDD <-%35; gerçek açılış dolumu modelden >30 bps kötü veya dolmayan giriş >%8.
