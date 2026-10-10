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
