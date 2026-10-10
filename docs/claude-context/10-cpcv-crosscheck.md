# 10 - CPCV capraz dogrulama: bizim `edge_validation/cv.py` vs skfolio

- Tarih: 2026-10-10. Script: `scripts/crosscheck_cpcv_skfolio.py` (skfolio yoksa "atlandi" yazar, cikis 0).
- skfolio **1.8.0**, lisans **BSD-3-Clause**; yalniz izole venv'de (scratchpad `sk_venv`) kuruldu. requirements/pyproject/repo .venv DEGISMEDI.
- Calistirma: `PYTHONPATH=. <sk_venv>/Scripts/python scripts/crosscheck_cpcv_skfolio.py`
- Parametreler: n_groups=n_folds=6, n_test_groups=n_test_folds=2, gunluk indeks, N=450..601.
  Bizde etiket ufku `t1 = t0 + p gun` (p bar overlap-purge), skfolio `purged_size=p`, `embargo_size=e`.

## Sonuclar

| Senaryo | N | p | e | split (biz/sk) | path (biz/sk) | yol kumesi | test gruplari | test idx esit | train ozdes | Jaccard ort/min |
|---|---|---|---|---|---|---|---|---|---|---|
| A purge=0 emb=0 | 600 | 0 | 0 | 15/15 (C=15) | 5/5 | esit | esit | 15/15 | 15/15 | 1.0000 / 1.0000 |
| B purge=0 emb=0, N%6!=0 | 601 | 0 | 0 | 15/15 | 5/5 | esit | esit | **0/15** | 0/15 | 0.9934 / 0.9901 |
| C purge=5 (t1=t0+5, emb 0) | 600 | 5 | 0 | 15/15 | 5/5 | esit | esit | 15/15 | 15/15 | 1.0000 / 1.0000 |
| D purge=5 emb=3, naif (emb_bars=3) | 600 | 5 | 3 | 15/15 | 5/5 | esit | esit | 15/15 | **1/15** | 0.9896 / 0.9842 |
| E purge=5 emb=3, esleme emb_bars=p+e=8 | 600 | 5 | 3 | 15/15 | 5/5 | esit | esit | 15/15 | 15/15 | 1.0000 / 1.0000 |
| F purge=0 emb=4 | 450 | 0 | 4 | 15/15 | 5/5 | esit | esit | 15/15 | 15/15 | 1.0000 / 1.0000 |

## Farklar (hata DEGIL, semantik)

1. **Kalanli N (B)**: biz `np.array_split` (artan N%G fazlasi ilk gruplara dagitilir); skfolio her fold `N//G`, kalan satirlar SON folda yazilir. Test kumeleri bu yuzden farkli; N%G==0 iken birebir ayni. Train Jaccard >= 0.99.
2. **Purge semantigi**: skfolio sabit sayida satir (`purged_size`) test oncesi ve sonrasi siler (etiket bilgisi gerekmez). Biz gercek etiket araligina (t0,t1) gore overlap'i atariz; t1=t0+p ile p satirlik purge iki tarafta (oncesi: b>=test_start, sonrasi: test_end=max t1 oldugundan) skfolio ile ayni cikar (C).
3. **Embargo (D vs E)**: skfolio embargo, purge'un USTUNE eklenir (sonra p+e satir). Bizde `embargo_bars` test-grubun son t0 konumundan sayilir ve etiket-bitisi ile `max` alinir (toplanmaz); bu yuzden `embargo_bars=e` < skfolio `p+e`. Esleme icin `embargo_bars = p + e` (E) gerekir. Bizim davranis (etiket sonrasi degil, grup sonundan sayim, max) AFML'ye uygun ve bilincli.
4. Gercek (degisken uzunluklu, cok sembollu) etiketlerde skfolio'nun sabit-satir purge'u yetersiz kalabilir; bizim zaman-tabanli purge sembol bagimsiz ve daha guvenli.
5. skfolio `split` test'i fold listesi olarak verir; biz birlestirilmis sirali indeks. Karsilastirmada birlestirilip siralandi.

## KARAR

Bizim `cv.py::CombinatorialPurgedCV` dogru: split sayisi C(N,k), path sayisi, path atamalari (her path'te her grup bir kez), test grup kumeleri ve (N%G==0 iken) test indeksleri skfolio ile birebir; purge/embargo uygun esleme ile (C, E, F) train kumeleri de ozdes (Jaccard=1). Yukaridaki farklar (kalan dagitimi, embargo sayim tabani) belgelenmis semantik farklardir; kod degistirilmedi.
