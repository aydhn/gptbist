# İlk ölçülmüş edge sonuçları (Adım 3 kapısı) — 2026-10-09

Veri: yfinance 1h, 19 likit BIST hissesi (tohum evren), ~730 gün, ham bar arşivi. Maliyet: `IntradayCostModel`
(komisyon 5 bps + BSMV %5 + borsa payı 0.3 bps + tick-yarım-spread + karekök etki; broker tarifesi doğrulanmadı).
Etiket: sonraki bar açılışı girişi, 4 bar ufku, seans sınırını aşmaz. Kapı: DSR≥0.95, PBO≤0.25, BH-FDR, reality check,
bootstrap CI alt sınırı>0, CPCV pozitif yol ≥%70.

| Aile | Olay | Brüt Sharpe | Net Sharpe | Karar |
|---|---|---|---|---|
| sma_trend | 716 | 0.17 | -2.24 | REJECTED |
| rsi_meanrev | 517 | -0.04 | -1.71 | REJECTED |
| breakout | 1345 | -2.48 | -4.79 | REJECTED |

Placebo (zamanlaması karıştırılmış sinyal) üç ailede de REJECTED: boru hattı gürültüde edge "bulmuyor".

**Sonuç:** Bu üç basit taban stratejide 1h ufkunda maliyet sonrası edge YOK; brüt getiri zaten sıfıra yakın,
maliyet (~23 bps gidiş-dönüş) onu net negatife çeviriyor. Bu, "edge yoktur" kanıtı değil, "bu üç kural, bu veri ve bu
maliyetle edge göstermedi" kanıtıdır. Kazanç vaadi yoktur.
