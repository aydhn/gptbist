# Gün içi araştırma notu (Adım 0) — 2026-10-09

Kısa özet; kaynaklar bağlantılı. Doğrulanamayan maddeler "?" ile işaretli. Kazanç vaadi yoktur.

## K1 — Ücretsiz BIST gün içi veri: derinlik ve gecikme
- **Gecikme:** Yahoo `.IS` (Borsa İstanbul) 15 dk gecikmeli, ICE Data Services kaynaklı
  ([Yahoo yardım](https://help.yahoo.com/kb/SLN2310.html)); borsa da verinin en az 15 dk gecikmeli olduğunu belirtir
  ([borsaistanbul.com](https://borsaistanbul.com/en/index/1/7/market)). Yahoo koşulları yeniden dağıtımı yasaklar ve
  veriyi "yalnız bilgi amaçlı" sayar → **yalnız yerel araştırma/paper**.
- **yfinance derinliği (resmî tablo bulunamadı, birden çok kaynak tutarlı):** 1m ≈ son 7 gün; 2m/5m/15m/30m ≈ son 60 gün;
  60m ≈ 730 gün (? tek ikincil kaynak). Çalışma zamanında her interval için sondaj testi yapılmalı (Yahoo değiştirebilir).
- **Sonuç:** 5 dk ile en fazla ~60 gün (~60 seans) geriye gidilir → walk-forward için yetersiz. **Kendi bar arşivi şart**:
  yerel parquet/SQLite, idempotent upsert (sembol+zaman anahtarı), boşluk/halt tespiti, her gün birikimli çekim.
  Geniş evrende (tüm BIST) istek hızı sınırı ve backoff gerekir (repoda yok).

## K2 — Gecikmeli veriyle gün içi edge ölçülebilir mi?
- **Yürütme edge'i (anlık sinyal→emir) ölçülemez/anlamsızdır:** veri 15 dk gecikmeli, paper dolum varsayımı uydurma olur.
- **Tarihsel sinyal kalitesi ölçülebilir ama güç sınırlı:** ~60 seans × ~500 hisse; seanslar arası bağımlılık yüzünden etkin
  örnek sayısı düşük. Deflated Sharpe / PBO için gereken deneme sayısı ve süre, arşiv birikmeden güvenilir sonuç vermez.
- **Dürüst öneri:** (1) hemen arşiv biriktirmeye başla; (2) edge iddiasını ancak ≥ 6–12 ay biriken 5/15 dk veri ve
  purged/CPCV + DSR + PBO kapısından geçince yap; (3) ara dönemde ufuk: **60 dk / seans içi swing** (730 gün derinlik,
  gecikme etkisi bar boyuna göre küçük) ve günlük-sinyal + gün içi giriş zamanlaması. 1 dk ufku önerilmez.

## Doğrulama yöntemleri
- **Purged/embargoed K-Fold, CPCV:** López de Prado, *AFML* (2018): etiketi test aralığıyla örtüşen eğitim örneklerini temizle (purge) +
  testten sonra embargo. sklearn `TimeSeriesSplit` yalnız örnek-sayısı `gap` ve `max_train_size` sunar; etiket bitiş zamanına
  göre purge ve embargo yok ([sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit)).
  Gün içi: etiket ufku seans sınırını aşıyorsa purge etiket-bitiş-zamanına göre yapılmalı.
- **PBO / CSCV:** [Bailey, Borwein, López de Prado, Zhu](https://papers.ssrn.com/abstract=2326253); tüm denenen konfigürasyonlar
  (başarısızlar dahil) kayda alınmalı, yoksa PBO aşağı yanlıdır. **Deflated Sharpe:** deneme sayısı, varyans, çarpıklık/basıklık düzeltmesi.
- LightGBM/XGBoost: sklearn uyumlu `fit/predict_proba`; kalibrasyon için `CalibratedClassifierCV` (zaman-sıralı veride `cv=` ile
  TimeSeriesSplit/öngörülü bölme). Henüz repoya bağımlılık eklenmedi (kararı Adım 4'te).

## BIST seans ve maliyet
- Açılış seansı 09:40 (emir toplama → 09:55 fiyat belirleme), sürekli işlem 10:00–18:00, kapanış seansı 18:00 sonrası
  (18:01–18:05 emir toplama, 18:05–18:07 fiyat belirleme, 18:08–18:10 kapanış fiyatından işlem); kapanış emirleri son
  fiyata göre ±%3 ([Borsa İstanbul](https://borsaistanbul.com/en/closing-session), [Garanti BBVA](https://www.garantibbva.com.tr/borsa-hisse-senetleri/bist-islem-saatleri)).
  Gün ortası tek fiyat bölümü (13:00–14:00) bazı kaynaklarda var, 2015 duyurusu kaldırıldığını söyler → **güncel resmî duyuruyla doğrulanmalı (?)**.
- Fiyat marjı günlük ±%10 (hisse; [Midas](https://www.getmidas.com/destek/borsa-istanbul/bist-piyasa-bilgileri/tavan-taban-uygulamasi-nedir/)); bazı kaynaklar
  eşik ve devre kesici (%5/15 dk?) için resmî teyit vermiyor (?).
- Tick: 0,01–19,99 → 0,01; 20,00–49,98 → 0,02; 50,00–99,95 → 0,05; ≥100 → 0,10 ([Borsa İstanbul fiyat marjları](https://www.borsaistanbul.com/en/price-bands)).
- Maliyet: aracı kurum komisyonu + borsa/Takasbank payı (+ BSMV, genelde %5; kurum tarifesinden teyit) — oranlar kuruma göre değişir,
  **parametre olarak yapılandırılmalı**.

## Repo karşılaştırması (Explore taraması; regex tabanlı, dosya içeriği doğrulanmadı)
| Yetenek | Durum | Yer |
|---|---|---|
| yfinance + local_file sağlayıcı | Var | `data/yfinance_provider.py`, `data/providers_v2/` |
| Retry/backoff, rate limit | **Yok** | — |
| Bar arşivi (SQLite/parquet yazma) | **Yok** (yalnız parquet import) | `data/importers/parquet_importer.py` |
| Gün içi bar boşluk dedektörü | Kısmi (günlük) | `data/incremental.py`, `data/reconciliation.py` |
| İstanbul tz, seans servisi | Var | `core/time_utils.py`, `calendar/session.py` |
| Resmî tatil tablosu, açılış/kapanış seansı, halt, tavan/taban | **Yok** | — |
| Walk-forward, purged CV, embargo | Var | `validation/walk_forward.py`, `purged_cv.py`, `splits.py` |
| CPCV, Deflated Sharpe, PBO | **Yok** (`validation/overfit.py`, `monte_carlo/reality_check.py` incelenecek) | — |
| Komisyon/slipaj/spread | Var | `costs/` |
| BSMV, tick size | **Yok** | — |
| PSI, model drift, registry, champion/challenger | Var | `drift/feature_drift.py`, `model_registry/`, `monitoring/champion_challenger.py` |
| KS, ADWIN | **Yok** (KS yalnız enum) | `drift/models.py` |
| Kelly | Taslak; vol-hedefleme sabit %20 | `risk/position_sizing.py` |
| Günlük azami zarar | **Yok** (yalnız sinyal sayısı sınırı) | `risk/filters.py` |
| Yinelenen takvim | `markets/calendar.py` ↔ `calendar/` (Adım 1c'de incele) | — |

## Canlı doğrulama (2026-10-09, THYAO.IS, yfinance 1.7.0)
- **1h derinliği ≈ 730 gün doğrulandı** (4368 bar/sembol, 2024-10 → bugün). 15m: 60 gün (1419 bar). K1 yanıtı güçlendi.
- **Bar hizası (İstanbul saati):** 1h → 09:30, 10:30 … 17:30 (9 bar/gün); 15m → 09:45 (açılış seansı baskısı), 10:00 … 17:45 (33); 5m → 09:55, 10:00 … 17:55 (97).
  `intraday/sessions.py` varsayılanı bu "yahoo" ızgarasıdır; son 4 haftada 1h/15m kapsama 1.000, 5m ≈ 0.998-0.999.
- Kapanış seansı (18:00-18:10) Yahoo barlarında görünmüyor; `closing_auction_window()` ayrı sunar.
- Yahoo tarafında 429/oran sınırı bu denemelerde tetiklenmedi; geniş evrende yine de `RateLimitedFetcher` (parti + aralık + backoff + devre kesici) kullanılır.
