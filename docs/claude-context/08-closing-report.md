# Blok L — Kapanış raporu (2026-10-10)

Gerçek emir yok, broker/API yok; yalnız paper/simülasyon. Aşağıdaki her şey ölçülmüş kanıttır; vaat yoktur.

## 1. Hangi aile / model geçti?
**Hiçbiri.** Sağlam edge (CandidateGate + v2 dayanıklılık + global-çoklu-test DSR + ADV≥5e7 + gecikme + alt dönem) bulunamadı.
- Kural-tabanlı aileler (önceki 14 + Blok I'in 5 yeni ailesi, 4 ufuk, iki komisyon senaryosu): **BAŞARISIZ** (hepsi REJECTED, `robust=N`). Tüm placebo'lar da REJECTED. Ayrıntı: `04-multiday-edge-results.md`, `06-block-i-results.md`.
- ML (`ml_xs_hgb` h=5): resmî koşuda CANDIDATE görünse de etiket batch-sırası artefaktıydı; deterministik havuzda geçerli aday sayılmaz → forward'da yalnız **WATCH**.
- Lifecycle uçtan uca (Blok K, gerçek arşiv, ~30 dk): baz model REJECTED (pbo), challenger REJECTED/FAILED_VALIDATION, `promote` BLOCKED, champion hâlâ yok. **Başarısız** (beklenen, güvenli).

## 2. Forward ilk bulgular
Henüz canlı gün yok. İlk `forward run-daily` STALE ile fail-closed durdu: Yahoo, 2026-10-09 hisse barlarını OHLC ile verirken Close/Adj Close alanını boş (NaN) veriyor; arşiv kapanışsız bar yazmaz. Kapı doğru çalışıyor. Piyasa açıldıktan sonra `daily archive-update --all-active` → `forward run-daily --receipt` elle koşulacak (ilk koşu ~11–15 dk). Başarı kriteri (≥60 canlı gün, EW + placebo'yu t≥2 ile yenme, DD<%20) ve geçersiz kılma eşikleri dondurulmuştur; yeniden ayar yapılmaz.

## 3. En iyi ölçülen reel CAGR vs %75
En iyi ölçülen reel CAGR ≈ **%27.7** (overlay ile ≈ %24.7, maxDD -%18). Hedef %75 **ULAŞILAMADI**; açık ≈ 47 puan. Bu rakam survivorship (delist semboller yok, sınır ölçülemez) ve TÜFE verisinin 2025-04'te bitmesi nedeniyle iyimserdir.

## 4. Bu oturumda tamamlananlar (özet)
- **H:** build_labels purge ertelenmiş çıkışa göre; global DSR havuzu ledger anlık görüntüsüne sabit (batch sırasından bağımsız, yalnız sıkılaştırır), efektif N raporlanır (gate ham N ile), smoke ledger ayrı, küçük evren kontrolü kapalı-başarısız; survivorship iyimserlik ifadesi her raporda.
- **I:** `--min-adv`, t+1 giriş gecikmesi raporu, başarı kriterleri fonksiyonu (`success_i.py`), 5 yeni aile, gerçek koşu.
- **J:** overlay paper giriş kapısına bağlandı (`RUNTIME_USE_DAILY_OVERLAY`, varsayılan kapalı); Türkçe işlem fişi + hash-zincirli emir-niyeti günlüğü + 100k TL tam hisse planı; stop/trailing/zaman-çıkışı ve gap/limit fonksiyonları + testler; aday başına paper-vs-backtest sapma raporu.
- **K:** HeartbeatManager depolaması, STALE_HEARTBEAT alarmı, orchestrator'da kill-switch/arama hatasında PAPER bloğu, forward integrity/backup/restore, izole kill-switch tatbikatı (11/11), Windows zamanlayıcı belgeleri (yalnız metin, hiçbir OS görevi oluşturulmadı).
- Test suite: 3199 → 3301 passed, 0 failed.

## 5. Kalan riskler ve açık işler
1. **Daily lifecycle asla CANDIDATE üretemez:** `DailyModelTrainer` kapıya tek-konfigürasyon grid veriyor, PBO hesaplanamıyor → her model WATCH/FAILED_VALIDATION. Güvenli ama challenger→promote yolu fiilen ölü. Çözüm (komşu grid) ledger N'yi şişirir → **kullanıcı kararı gerekli**.
2. **Drift tetikleyicisi aşırı hassas olabilir:** en güçlü uyarılar piyasa düzeyi özelliklerde (tarih başına tek değer; ~60 bağımsız gözlem, KS p-değerleri anlamsız).
3. **Lifecycle hiçbir CLI/runtime adımına bağlı değil;** `daily-train --only-if-due` var ama zamanlayan yok (belgede metin olarak).
4. **Stop/trailing/gap fonksiyonları paper motoruna bağlı değil** (paper motorunda otomatik stop yoktu; bağlamak yeni bir çıkış izleyicisi gerektirir; `PAPER_GAP_AWARE_EXITS` eklenmedi).
5. **Overlay paper kapısı:** NAV zaten küçültülmüş olduğundan overlay'in gördüğü düşüş gerçeğinden hafif; ölçek saf backtest'ten az muhafazakâr olabilir.
6. **Preflight yerelde "8 secret leaks in configuration" veriyor** (muhtemelen .env; incelenmedi) → promosyonu doğru biçimde engelliyor, ama .env/.env.example içeriği gözden geçirilmeli.
7. **Fiş fiyatları** `as_of` kapanışı; shadow simülasyonu ertesi açılışta giriyor → tutarlar tahmindir.
8. **H5 yapılmadı:** VBTS / tek fiyat / brüt takas olayları için doğrulanmış RESMÎ açık dosya/API bulunamadı; HTML scraping yapılmadı. Dolum modelinde "tedbirli hisse alınmaz/satılamaz" kuralı YOK.
9. Doğrulanmamışlar: 2026 dini tatiller, fiyat limiti geçiş tarihi (2020-03-01), delist verisi yok, TÜFE 2025-04'e kadar.
10. Eski `daily_all` raporlarında `snapshot_rowid` yok; `select_v2` onları yok sayar (forward portföyleri dondurulmuş, etkilenmez). Yeni portföy seçimi için batch yeniden koşulmalı.
11. Yedekleme koşu kilidi almaz: `run-daily` sonrası alınmalı.

## 6. Bir sonraki adım
1. Piyasa açıldığında veri tazele → `forward run-daily --receipt` (+ `forward health`, `forward integrity`, `forward backup`).
2. Kullanıcı kararları (aşağıda) gelince yer tutucuları güncelle.
3. 60+ canlı gün biriktir; yeniden ayar yapma.

## Kullanıcıya sorular (engellemiyor; yer tutucularla devam edildi)
1. Gerçek mevduat/repo faizi + stopaj (şimdi %30 / %15 yer tutucu).
2. `data/macro/cpi_tr.csv` için güncel TÜFE (2025-04'ten sonrası).
3. Komisyon dışı gerçek maliyetler (BIST payı, BSMV, takasbank) hesap dökümünden.
4. Forward paper için günlük çalıştırma saati ve makinenin her gün açık olup olmadığı.
5. 12 aylık forward geçersiz kılma eşiklerinin onayı.
6. Lifecycle için komşu-grid (PBO) kararı: N şişmesini kabul eder misiniz?
7. VBTS/tek fiyat/brüt takas için elinizde resmî bir dosya/kaynak var mı?
