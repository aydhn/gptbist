# BIST Sinyal Botu

## Projenin Amacı
Borsa İstanbul (BIST) evreninde çalışacak, ücretsiz araçlara dayalı, yerel bilgisayarda çalışabilen ve yüksek kaliteli sinyal üretmeyi hedefleyen algoritmik bir işlem/sinyal sistemidir. Bu sistem, gelişmiş backtest, risk yönetimi ve makine öğrenimi bileşenlerini bir araya getirerek filtreli ve yüksek kaliteli araştırma çıktıları sunmayı amaçlamaktadır.

## Yasal ve Finansal Uyarı
**DİKKAT:** Bu sistem herhangi bir "yatırım tavsiyesi" vermediğini açıkça beyan eder. Üretilen tüm çıktılar yalnızca "algoritmik sinyal" ve "araştırma çıktısı" niteliğindedir. Alım-satım kararlarınızı kendi risk profilinize ve değerlendirmelerinize göre veriniz. Geçmiş performans gelecekteki sonuçların garantisi değildir.

## Ne Değildir?
- **HFT (Yüksek Frekanslı İşlem) Değildir:** Saniyede onlarca işlem hedeflenmez.
- **Garanti Kazanç Sistemi Değildir:** Piyasada hiçbir sistem garanti kazanç sunamaz.
- **Ücretli API Gerektirmez:** Tamamen ücretsiz ve erişilebilir veri kaynaklarıyla çalışacak şekilde tasarlanmıştır.
- **Dashboard Değildir:** Web tabanlı bir kullanıcı arayüzü (Streamlit, Dash, vb.) barındırmaz; bildirimler Telegram üzerinden iletilir.

## Teknik Sınırlar
- Python 3.11+ tabanlı.
- Ücretli veri servisleri, API'ler (OpenAI, X/Twitter, Bloomberg vb.) veya bulut altyapıları gerektirmez.
- HTML scraping/web kazıma kesinlikle yasaktır.
- Ortalama bir Windows/Linux yerel bilgisayar donanımında çalışabilir. GPU zorunlu değildir.
- Gerçek zamanlı (canlı) emir gönderimi (broker entegrasyonu) ilk fazda desteklenmemektedir, öncelik sinyal üretimi, paper trading ve backtesting'dir.

## Kurulum
1. Repoyu klonlayın.
2. Bir sanal ortam (virtual environment) oluşturun: `python -m venv venv`
3. Sanal ortamı aktif edin: `venv\Scripts\activate` (Windows) veya `source venv/bin/activate` (Linux/Mac)
4. Bağımlılıkları yükleyin: `pip install -r requirements.txt`

## .env Kullanımı
Sistem ayarları ortam değişkenleri (environment variables) kullanılarak yönetilir.
1. Kök dizindeki `.env.example` dosyasını kopyalayarak `.env` adında yeni bir dosya oluşturun.
2. `.env` dosyası içindeki değerleri kendi yapılandırmanıza göre düzenleyin. (Not: `.env` dosyası `.gitignore` ile repodan dışlanmıştır.)

## İlk Çalıştırma
Sistemin sağlıklı çalışıp çalışmadığını kontrol etmek için terminal üzerinden şu komutu çalıştırabilirsiniz:
```bash
python -m bist_signal_bot
```
Bu komut; ayarları yükleyecek, logger'ı başlatacak ve bir "Healthcheck" (Sağlık Kontrolü) raporu sunacaktır.

## Faz Bazlı Geliştirme Notu
Bu proje 100 fazlık büyük bir vizyonun **Phase 1 (Faz 1)** çıktısıdır. Tüm mimari kararlar, ileride eklenecek modüllerin kolayca entegre edilebileceği genişletilebilir bir yapı düşünülerek alınmıştır.

## Mimari Modüller
- **core:** Uygulama genelinde kullanılan sabitler, hatalar ve loglama yapılandırmaları.
- **config:** Ortam değişkenleri ve uygulama ayarlarının merkezi olarak yönetilmesi.
- **data:** Veri sağlayıcıları (yfinance, vb.) için soyut arayüzler ve modeller.
- **indicators:** Teknik indikatör hesaplamaları.
- **signals:** Sinyal veri modelleri ve puanlama (scoring) mantığı.
- **strategies:** Temel strateji soyutlamaları.
- **risk:** Risk yönetim motoru için temel arayüzler.
- **backtesting:** Geçmiş veri üzerinde strateji testi arayüzleri.
- **ml:** Makine öğrenimi model entegrasyonları için arayüzler.
- **optimization:** Strateji parametre optimizasyonu (Optuna vb.).
- **regimes:** Piyasa rejimi (trend, yatay, volatil vb.) tespiti.
- **notifications:** Telegram vb. bildirim entegrasyonları.

## Phase 1 Çıktıları
- Temel proje iskeleti ve paket yapısı (bist_signal_bot/) oluşturuldu.
- `pydantic-settings` tabanlı konfigürasyon (`settings.py`) entegre edildi.
- Sistem bilgilerini özetleyen Healthcheck modülü geliştirildi.
- Soyut (Abstract) sınıflar kullanılarak gelecekteki modüller için (veri, strateji, backtest, ml, optimizer, vb.) arayüzler tanımlandı.
- Temel loglama, istisna (exception) yönetimi ve pytest için smoke testler hazırlandı.

## Phase 2 Çıktıları
- **Sembol Standardı:** Sistemin iç sembol formatı (örn. `ASELS`) olarak belirlenmiş olup, veri sağlayıcıya özgü ekler (örn. `.IS`) izole edilmiştir.
- **YFinance Formatı:** Sadece veri çekimi sırasında kullanılan `ASELS.IS` formatına dönüştürme ve tersi işlemler için utility'ler eklendi.
- **Seed Sembol Listesi:** Sistemin ilk aşamada test edilebilmesi için `DEFAULT_SEED_SYMBOLS` adında, likit hisselerden oluşan bir başlangıç listesi eklendi. **Bu liste güncel endeks kompozisyonu (BIST30/BIST100 vb.) iddiası taşımaz.** Sadece sistemin bootstraplenmesi içindir.
- **Evren Genişletilebilirliği:** BIST evreninin ileride data provider'lar veya manuel listeler üzerinden güncellenebileceği esnek bir `SymbolUniverse` sınıfı yazıldı.
- **Güvenlik:** Phase 2 kapsamında da hiçbir canlı internet bağlantısı yapılmaz ve web scraping/HTML parsing tekniklerine yer verilmez.

## Phase 3 Çıktıları
- **Data Provider Mimarisi:** Botun veri katmanı, bağımsız provider (sağlayıcı) arayüzleriyle (BaseMarketDataProvider) soyutlanmıştır. Doğrudan yfinance çağırmak yerine bu mimari benimsenmiştir.
- **YFinance Adapter:** yfinance kütüphanesi için bir adaptör eklendi. Testlerde dış bağımlılığı engellemek adına doğrudan internet çağrısı yapmaz.
- **Mock Provider:** Çevrimdışı ve deterministik fiyat verisi üretilmesi için eklendi. Testlerde bu yapıyla kararlı testler koşturulur.
- **Güvenlik ve Performans:** HTML scraping (web kazıma) kesinlikle engellendi, sadece resmi ve ücretsiz Python kütüphanesi adapterları desteklenecek. İleride önbellekleme (cache) için DataService katmanı ayrıldı.

## Phase 4 Çıktıları
- **Yerel Veri Deposu (Local-First Storage):** İnternet bağımlılığını azaltmak, veri tekrar indirme sorununu gidermek ve geçmişi yerel dosya sisteminde tutmak için `LocalMarketDataStore` entegre edildi.
- **CSV Storage Kararı:** Veriler başlangıç formatı olarak Windows uyumlu, insan tarafından okunabilir, ekstra bağımlılık (örn. PyArrow) gerektirmeyen CSV formatında saklanır. Parquet desteği, genişletilebilir tasarım sayesinde opsiyonel/sonraki fazlara bırakılmıştır.
- **Dosya Yolu Standardı:** Veriler `data/market_data/ohlcv/{provider}/{timeframe}/{symbol}.csv` şeklinde organize edilir.
- **Metadata Index:** Kaydedilen dosyaların durumu, satır sayısı, başı/sonu ve güncellenme tarihleri `market_data_index.json` dosyasıyla takip edilir.
- **Cache Entegrasyonu:** `MarketDataService` içerisine store mantığı giydirildi. `get_ohlcv` metodu önce local store'a bakar; mevcutsa doğrudan döner, mevcut değilse veya `refresh=True` geçilmişse provider'dan çeker ve doğrulamadan geçirip local store'a kaydeder.
- **Güvenlik ve Testler:** HTML scraping (web kazıma) kesinlikle engellendi, ücretsiz API limitleri korundu ve yazılan storage testlerinin internet gerektirmemesi sağlandı.

## Phase 5 Çıktıları
- **Veri Kalite Kontrol Sistemi:** BIST sinyal botunun kullandığı OHLCV verilerinin güvenilirliğini test etmek ve ML/Backtest öncesi doğrulama yapmak için `DataQualityChecker` eklendi.
- **Kontroller:** Boş veri, eksik kolonlar, index sıralaması ve duplicate'leri, negatif değerler (fiyat/hacim), OHLC ilişkisi (High >= Low vb.), sürekli sıfır hacim, büyük tarih boşlukları ve ekstrem getiri anormallikleri.
- **Skorlama:** Her veri kümesine 0-100 arası bir skor verilir. Empty Data gibi durumlar `CRITICAL` seviyededir ve geçerlilik (`passed`) durumu `False` döner.
- **Storage Ayrımı:** `LocalMarketDataStore` sadece veriyi diskte saklama ile sorumluyken, okuma/yazma sırasındaki kalite denetimleri `MarketDataService` içerisine entegre edilerek sorumluluklar ayrıldı.
- **Güvenlik ve Performans:** Phase 5 boyunca internet bağlatısı yapılmadı. `MarketDataService` için `fail_on_quality_error` parametresi ile kontrol sıkılığı ayarlanabilir yapıldı.

## Phase 6 Çıktıları
- **BIST İşlem Takvimi ve Seans Mantığı:** Sistemin işlem günlerini, seans içi/dışı durumlarını ve sinyal üretme zamanlamasını doğru yorumlayabilmesi için `BistMarketCalendar` ve `BistMarketSessionService` bileşenleri geliştirildi.
- **Yerel ve Yapılandırılabilir Takvim:** Resmi tatil takvimi için scraping (web kazıma) yapılması yasak olduğundan, takvim yerel ve ".env" üzerinden yönetilebilir bir mimariyle kuruldu. İsteyen kullanıcılar `BIST_MANUAL_HOLIDAYS` parametresine virgülle ayrılmış ISO tarihleri (örn: `2026-01-01,2026-04-23`) vererek kendi tatillerini ekleyebilirler. Hafta sonları (Cumartesi/Pazar) standart olarak kapalı kabul edilir. Bu sistem, resmi tatil listesi iddiası taşımaz ("local configurable exchange calendar").
- **Seans Durumları (Session Logic):** PRE_MARKET, REGULAR, POST_MARKET, CLOSED, HOLIDAY, WEEKEND gibi seans durumlarını yönetebilecek esneklik sağlandı.
- **Sinyal Zamanlaması:** Günlük (`daily`) ve seans içi (`intraday`) sinyal üretimi için zamanlama kuralları tanımlandı. Örneğin; günlük sinyal, piyasa kapandıktan sonra (varsayılan: kapanış + 15 dakika) tetiklenecek şekilde kurgulandı.
- **Backtest Uyumluluğu:** Geliştirilen bu takvim katmanı, ilerideki backtesting ve makine öğrenimi süreçlerinde tarih doğrulama adımları için hazır bir temel sunmaktadır.

## Phase 7 Çıktıları
- **Telegram Bildirim Altyapısı:** BIST Signal Bot'un dashboard, web panel veya HTML scraping kullanmadan, Telegram üzerinden güvenilir ve izole bir bildirim katmanı oluşturuldu. `TelegramNotifier` ve `MockNotifier` yapılarıyla test edilebilir ve mocklanabilir bir tasarım hedeflendi.
- **Güvenlik ve Çevre Değişkenleri:** `.env` dosyası üzerinden `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_DRY_RUN`, `TELEGRAM_PARSE_MODE` değerleri okundu ve loglarda bu secret'ların (`TELEGRAM_BOT_TOKEN`) sızdırılmaması için `__repr__` davranışına maskeleme (mask_secret) eklendi.
- **Notification Modelleri ve Formatter:** Sistemin göndereceği mesajların tip ve limitlerini standartlaştıran Pydantic modelleri (`NotificationMessage`) ile okunaklı ve mobil cihaza uyumlu mesaj metni üreten `NotificationFormatter` tasarlandı. HTML parse hatası almamak için özel karakterler escape ediliyor. Uzun hata ve rapor mesajları limitlere göre güvenli bölünüyor (`split_message`).
- **Rate Limiter (Zaman Kısıtlayıcı):** Mesajların Telegram limitlerini (örn: 1 saniyede maksimum mesaj) aşmaması için `NotificationRateLimiter` eklendi. Ayrıca hata (`ERROR`/`CRITICAL`) bazlı mesaj yığılmalarını engellemek üzere, 5 dakikada (300 saniye) bir hata başı tek mesaj atılabilmesine olanak tanıyan `error_cooldown_seconds` mekanizması devreye alındı.
- **Dry-Run Mode ve Test Güvenliği:** `TELEGRAM_DRY_RUN` devrede iken, notifier sadece simüle edilmiş sonuçlar döner (ağ/network işlemi yapılmaz). Testlerde doğrudan Telegram API çağrısı yapılmaması (`mock_send_raw`) için monkeypatch mimarisi oluşturuldu, kodun hiçbir yerinde canlı Telegram request bağımlılığı kurulmadı.

## Phase 8 Çıktıları
- **Loglama Mimarisi:** Botun çalışabilirliğini izlemek için sistem `bist_signal_bot.log` üzerinden opsiyonel (ve Rotating File Handler özellikli) loglama yeteneğine kavuşturuldu. Terminal çıktısı ile dosya çıktısı birleştirildi.
- **Audit Trail (Denetim İzi):** Olay tabanlı (`APP_START`, `HEALTHCHECK`, `DATA_FETCH`, `ERROR`, vb.) durumların yapısal (`JSONL`) formatında izlenebilmesi için `audit.log` mekanizması oluşturuldu.
- **Hata Yönetimi ve Telegram Bildirimleri:** Tüm beklenen ve beklenmeyen hatalar `ErrorHandler` ile merkezileştirildi. Hataların bağlamı (context) hassas verilerden arındırılarak loglanır ve konfigüre edilmişse Telegram'a sadece `ERROR` veya `CRITICAL` seviyesindeki hatalar yollanır.
- **Operasyonel Güvenlik:** Sinyal dili için `OperationalSafetyError` ("kesin kazanır" gibi yasaklı kelimeler için) oluşturuldu ve loglanmadan/mesaj atılmadan önce API anahtarları, token'lar ve şifrelerin maskelenmesini (`***`) sağlayan `core/safety.py` entegre edildi.
- **Run ID (Runtime Context):** Uygulama her başladığında kısa bir UUID (Run ID) üretilerek oluşan logların ve audit event'lerin hangi çalışmaya ait olduğu korele edilebilir hale getirildi.

## Phase 9 Çıktıları
- **Config Sistemi:** Tüm uygulama ayarlarının pydantic-settings üzerinden merkezileştirilmesi (`config/settings.py`).
- **Çevre Değişkenleri (.env):** `env_loader.py` ile `.env` dosyasının güvenli yüklenmesi ve sağlık kontrolleri için durumunun belirlenmesi eklendi. `.env.example` hazırlandı.
- **Ortam Profilleri:** `config/profiles.py` ile `development`, `test`, ve `production` ortamlarına özgü farklı varsayılan davranışlar (DRY_RUN, LOG_LEVEL) kodlandı.
- **Güvenli Secret Yönetimi:** `config/secrets.py` içerisinde "token", "chat_id" vb. barındıran hassas değişkenlerin loglanmadan önce veya string'e çevrilmeden önce maskelenmesini (`secr...1234` vb.) sağlayan fonksiyonlar kurgulandı. `Settings` objesinin repr metodu da bunu kullanacak şekilde güncellendi.
- **Gelişmiş Validasyon:** `config/validation.py` sayesinde yanlış konfigürasyonlara `ConfigurationError` fırlatılarak hataların "fail-fast" mantığında yakalanması sağlandı. `APP_ENV="production"` olduğunda `DEBUG_TRACEBACKS` açık olmaması gibi ekstra üretim ortamı kontrolleri eklendi.
- **Ayrıştırılmış Sorumluluk:** Ayarların ML, Backtest, Risk, Telegram vb. kategorilere ayrılarak ilerideki fazlarda sadece kendi ilgi alanındaki ayarları genişletmesine zemin hazırlandı.


## Phase 10: CLI Operations Center

This bot runs purely from the terminal and doesn't rely on web dashboards, streamlining operations directly on the command line.

### Available Commands:
- `python -m bist_signal_bot healthcheck` : Basic bot and environment healthcheck summary.
- `python -m bist_signal_bot config` : Output the active settings (safely masks tokens).
- `python -m bist_signal_bot symbols` : List the default BIST seed symbol universe.
- `python -m bist_signal_bot validate-symbol <symbol>` : Normalize and validate a symbol.
- `python -m bist_signal_bot provider-status` : Show status and configuration of the active data provider.
- `python -m bist_signal_bot storage-status` : Display local filesystem paths and writability.
- `python -m bist_signal_bot calendar-status` : Display current session market times.
- `python -m bist_signal_bot telegram-test` : Sends a dry-run or actual test message via TelegramNotifier.
- `python -m bist_signal_bot mock-data <symbol>` : Deterministically generates mock stock data for debugging.
- `python -m bist_signal_bot quality-demo <symbol>` : Tests the DataQualityChecker directly on mock data.
- `python -m bist_signal_bot version` : Outputs python and platform system diagnostic version information.
- `python -m bist_signal_bot diagnose` : Comprehensive diagnostic command running config and healthcheck outputs safely.

*To output most commands as parseable data, append the `--json` flag to the arguments list.*


## Phase 11: OHLCV Data Downloader & CLI Integration
- Implemented `MarketDataDownloader` to download single or multiple symbols cleanly with error handling.
- Batched operations support `--all` for active universe, and `--group` to target subsets.
- Refresh `--refresh` parameter bypasses the cache to fetch directly from the provider.
- Skip saving to the local database via the `--no-save` flag.
- Integrates seamlessly with existing data quality checks (Score is recorded).
- Fully deterministic offline testing with the `MockMarketDataProvider`—No HTML scraping, no paid API hooks.
- Configurable settings via `settings.py` for retry limits, symbol caps, and defaults.
- Telegram Summary support.
- Fully wired into the CLI: `python -m bist_signal_bot download-data ASELS`

## Phase 14 Çıktıları
- **Data Cleaning Katmanı**: İndirilen OHLCV verilerindeki eksik, hatalı ve aykırı durumları handle eden `MarketDataCleaner` entegre edildi. Normalization ile formatı düzeltilen veri bu adımda mantıksal olarak düzeltilir.
- **Politikalar**:
  - Missing Values: İleri/geri doldurma veya boşluk silme.
  - Invalid OHLC: Mantıksız open/high/low/close ilişkilerini düşürme.
  - Duplicate Timestamp: İlkini tut, sonuncuyu tut veya hata ver.
  - Outliers (Aykırı Değerler): Extreme volume veya getiri durumları sadece işaretlenir (Flag Only), varsayılan olarak silinmez (bölünmeler/sermaye artırımları olabileceği için).
- **Entegrasyon**: `MarketDataService` içerisine dahil edildi ve her `get_ohlcv` çağrısında veriler temizlenerek quality checker'a öyle iletilir. Bu sayede veriler temizlendikten sonra kalitesi test edilir.
- **Raporlama**: Temizleme süreci sonrası ne kadar satır/değer silindiği veya doldurulduğu `CleanedMarketData` objesi içinde raporlanır ve Metadata içerisine yazılır.
- **Sıradaki Faz**: Phase 15'te "Bedelsiz bölünme, Temettü vb. Kurumsal Aksiyon (Corporate Actions) düzeltmeleri" yapılacaktır. Bu faza kadar Extreme Return/Volume davranışları bu nedenle silinmez bırakılmıştır.


## Phase 17: Trend Indicators, Feature Set & Trend Regime Preparation

**Amacı:** BIST Signal Bot'un trend yönünü, gücünü ve kırılımlarını ölçmesi için kapsamlı trend indikatörlerinin geliştirilmesi.
- **Trend Feature ve Sinyal Arasındaki Fark:** Bu fazdaki hesaplamalar al/sat sinyali üretmez, stratejilerde (ML veya rule-based) kullanılabilecek matematiksel/durumsal öznitelik skorları üretir.
- **Eklenen Trend İndikatörleri:**
  - Moving Average Distance, Crossover State, Crossover Event, Slope
  - Price Above MA, Consecutive Above/Below MA Count
  - Donchian Channel, Keltner Channel
  - ADX / DMI, Aroon
  - Ichimoku Components, Supertrend, Linear Regression Slope
  - Trend Strength Composite (Skor hesaplama)
- **Look-Ahead Bias Önlemi:**
  - Donchian breakout gibi modellerde `.shift(1)` kullanılarak look-ahead önlenmiştir.
  - Ichimoku için ileriye dönük (forward-shifted) veri grafikte anlamlı olsa da, veri seti (ML/backtest) için look-ahead bias yaratacağından ham (raw) component olarak kullanılmıştır.
- **Çalıştırma ve Backtest:**
  - `python -m bist_signal_bot trend-features ASELS --source mock --level basic` komutlarıyla backtest/ML modeli için detaylı data kolonları (features) oluşturulur.
- HTML scraping yapılmamış, ücretli API kullanılmamıştır.


## Phase 19: Volatility Indicators, Feature Set & Risk Regime Preparation

**Amacı:** BIST Signal Bot'un fiyat oynaklığını, volatilite sıkışmasını/genişlemesini, ATR tabanlı risk ölçümlerini, range bazlı volatiliteyi, gap riskini ve ileride risk/rejim/pozisyon boyutlandırma modüllerinde kullanılacak volatilite feature setlerini ölçebilmesi için kapsamlı volatilite indikatörleri katmanını geliştirmek.
- **Volatility Feature ve Sinyal Arasındaki Fark:** Bu fazdaki hesaplamalar al/sat tavsiyesi/sinyali üretmez, stratejilerde (ML veya rule-based) kullanılabilecek matematiksel/durumsal öznitelik skorları üretir. Compression/expansion skorları finansal tavsiye değildir.
- **Eklenen Volatilite İndikatörleri:**
  - ATR Percent ve Normalized True Range
  - Historical Volatility ve Realized Volatility
  - Parkinson, Garman-Klass ve Rogers-Satchell Volatility
  - Range Percent ve Gap Percent (Risk Feature'ları)
  - BB Width Percentile ve ATR Percentile (Sıkışma/Genişleme mantığı)
  - Volatility Z-Score, Compression Score, Expansion Score
  - Volatility Regime Feature (Risk/rejim için kullanılacak) ve Volatility Composite Score
- **Look-Ahead Bias Önlemi ve Güvenlik:**
  - Logaritmik formüllerde sıfır veya negatif fiyatların neden olabileceği matematiksel hatalara karşı (örn `Garman-Klass`) güvenli maskeleme ve clipping uygulanmıştır. Negatif varyans üretebilecek durumlar önlenmiştir. Gelecek mum verisi kullanılmaz.
- **Çalıştırma ve Özellik Üretimi (Feature Generation):**
  - `python -m bist_signal_bot volatility-features ASELS --source mock --level basic` komutlarıyla backtest/ML modeli ve risk engine için detaylı data kolonları (features) oluşturulur.
- HTML scraping yapılmamış, ücretli API kullanılmamıştır. Tamamen yerel (local-first) altyapı üzerinde çalışır.

## Phase 21: Pattern, Breakout, and Price Action Feature Layer

Phase 21 introduces an extensive library of pattern detection components designed to extract robust technical features without look-ahead bias:
- **Candle Patterns**: Detects inside/outside bars, engulfing, doji, and hammer approximations.
- **Price Structure**: Detects rolling higher highs / lower lows, range position, and range compression.
- **Breakouts**: Identifies price breakouts, volume-confirmed breakouts, lagged false breakouts, and retests. To prevent data leakage, historical confirmation is rigorously applied to pseudo-future patterns like false breakouts.
- **Support & Resistance**: Dynamically tracks rolling SR levels and pivot points utilizing strict `shift(1)` isolation, avoiding baseline leakage.

This layer purely emits calculated features for backtesting and ML ingestion; it explicitly does **NOT** issue financial or trading advice. As per the strict requirements, there is no dashboard, HTML scraping, paid API integration, or real-order execution. Check out the available tools using `python -m bist_signal_bot patterns list` and `python -m bist_signal_bot pattern-features ASELS --source mock --level full`.

### Phase 22: Divergence Engine & Feature Layer
- **Divergence Engine Goal:** Detect price-indicator discrepancies (divergences) natively without look-ahead bias to provide rich ML/backtest features.
- **Regular Divergence:** Detects potential trend reversals (e.g. Price Lower Lows but Indicator Higher Lows -> Regular Bullish).
- **Hidden Divergence:** Detects trend continuation signals (e.g. Price Higher Lows but Indicator Lower Lows -> Hidden Bullish).
- **Pivot Detection Modes:**
  - `LOOKBACK_ONLY` (Default): Uses only past lookback window to find extremes. No look-ahead bias, suitable for real-time feature generation.
  - `CONFIRMED_LAGGED`: Wait for confirmation bars. Highly reliable but features are artificially delayed by confirmation lag to avoid future leakage in backtests.
- **Supported Indicators:** Native support via short-hand mappings (`rsi`, `macd_hist`, `obv`, `mfi`, `stoch_k`, `ppo_hist`, `cmf`, `momentum`).
- **Strength Score:** A composite heuristic score (0-100) assessing magnitude and duration of divergence. *Note: this is not a financial recommendation.*
- **Usage via CLI:**
  - `python -m bist_signal_bot divergence detect ASELS --source mock --level basic`
  - `python -m bist_signal_bot divergence detect ASELS --source mock --indicators rsi macd_hist`
- **Output:** Outputs dataframe columns like `div_regular_bullish_rsi`, `div_strength_rsi`, and `div_bars_since_last_rsi` suitable for ML models.
- **No GUI, No Web Scraping:** This phase conforms strictly to the local-first CLI architecture.

### Phase 23: Çoklu Zaman Dilimi Sistemi ve Multi-Timeframe Feature Katmanı
BIST Signal Bot artık çoklu zaman dilimi (multi-timeframe) mimarisine sahiptir. Bu sistem, günlük, haftalık, aylık veya intraday verileri look-ahead bias yaratmadan tek bir veri setinde hizalayabilir. Üst zaman diliminden gelen bar bilgileri (`shift_higher_tf_by_one_bar=True`) ile kaydırılarak yalnızca kapanmış barlar alt timeframe satırlarına taşınır.

**Özellikler:**
- **Resample Kuralları:** OHLCV mantığıyla bar aggregation. Eksik/yarım kalan son barlar filtrelenebilir.
- **Alignment Modes:** `CLOSED_BAR_ONLY` (varsayılan) ile sadece bitmiş olan periyodlar değerlendirilir.
- **MultiTimeframeFeatureBuilder:** `basic`, `advanced` ve `full` feature level seçenekleriyle otomatik SMA, RSI, ATR, vb. eklentileri yapar.
- **Prefix Standardı:** Çakışmaları engellemek için `w_`, `m_` prefixleri kullanılır.
- **CLI Entegrasyonu:** `python -m bist_signal_bot mtf-features ASELS --source mock --level full`
- HTML scraping veya ücretli veri kaynağı kullanılmaz, tamamen mevcut altyapıya bağımlıdır.

## Phase 24: Strategy Architecture
- **Strategy Architecture**: Establishes a professional strategy engine capable of running research, backtests, paper trading, and live signals. Defines strict input/output contracts.
- **Strategy vs Indicator**: Strategies use indicators and features to make directional determinations (LONG/SHORT/FLAT), whereas indicators just provide raw data.
- **SignalCandidate Model**: Represents a trade intent (direction, score, confidence, reasons, risk notes).
- **Not Orders / Not Advice**: The system only produces "Research signal candidates". It sends NO orders, connects to NO brokers, and issues NO investment advice.
- **BaseStrategy Lifecycle**: Validation of context and parameters -> Feature preparation -> Candidate generation -> Result aggregation.
- **Registry & Engine**: `StrategyRegistry` manages available strategies. `StrategyEngine` orchestrates execution.
- **Builtin Baseline Strategies**:
  - `moving_average_trend`: simple crossover.
  - `rsi_mean_reversion`: oversold/overbought baseline.
  - `breakout_volume`: volume confirmed highs/lows.
  - `composite_feature`: aggregates trend, momentum, and volume.
- **CLI Commands**:
  - `strategies list`
  - `strategies run`
  - `strategies batch`
- **Future Preparations**: This lays the foundation for backtest modules, machine learning filters, and automated optimization, while preventing look-ahead bias and avoiding web-scraping/paid APIs.

## Phase 25: Baseline & Benchmark Strategies

The purpose of this phase is to provide simple, transparent, deterministic, and testable benchmark strategies against which we can compare other algorithmic signals. This creates a reference performance layer to answer whether a custom strategy is actually generating alpha over naive approaches.

**Key Concepts:**
* **Reference Output**: Benchmark outputs are purely for reference and comparison. They do not claim to provide alpha and are not investment advice.
* **Buy-and-Hold**: A continuous LONG reference strategy for a given symbol.
* **Cash**: A continuous FLAT reference representing a 100% cash position.
* **Equal-Weight**: Evaluates multiple symbols and assigns equal weights to each.
* **Moving Average**: A basic reference strategy going LONG when price > SMA, else FLAT.
* **Naive Momentum**: Evaluates whether the N-period return is positive.
* **Naive Volatility Filter**: Returns LONG when historical volatility is within limits, else FLAT.
* **Deterministic Random Baseline**: Generates pseudo-random deterministic signals strictly as a "sanity check" baseline.

These benchmarks are registered within `BenchmarkRegistry` and executed via the `BenchmarkEngine`. We intentionally separate benchmarks from `StrategyRegistry` to keep their purposes distinct in our architecture.

**Usage:**

List all available benchmarks:
```bash
python -m bist_signal_bot benchmarks list
```

Run a benchmark for a symbol:
```bash
python -m bist_signal_bot benchmarks run ASELS --source mock --benchmark moving_average_benchmark --param window=200
```

Run a batch benchmark on multiple symbols:
```bash
python -m bist_signal_bot benchmarks batch --benchmark equal_weight --symbols ASELS THYAO GARAN --source mock
```

Run default benchmarks for comparison on a symbol:
```bash
python -m bist_signal_bot benchmarks default ASELS --source mock
```

*Note: No real orders are sent. No HTML scraping is performed. No paid APIs are used.*

## Phase 26: Cost, Slippage & Spread Model

The BIST Signal Bot includes a robust transaction cost model designed to simulate realistic Borsa Istanbul conditions. It is specifically built to enable realistic backtesting and paper trading performance metrics.

### Key Features
- **Commission Model:** Supports fixed amounts, basis points (BPS) and hybrid formats.
- **Slippage Model:** Includes fixed BPS, volume-based (using square root of participation), volatility-based, and hybrid slippage models.
- **Spread Model:** Estimates market spread based on a symbol's liquidity bucket (High, Medium, Low) derived from its average daily turnover.
- **Cost Scenarios:** Test varying market conditions using `OPTIMISTIC`, `BASE`, `CONSERVATIVE`, and `STRESS` scenarios.

**IMPORTANT:**
This bot does **NOT** know your actual brokerage commission rates, exchange fees, or exact market slippage. The default configuration uses professional but conservative estimations. You must configure your specific commission rates in your `.env` file for accurate modeling. This bot does **NOT** place real orders, scrape HTML, or use paid APIs.

### Configuration
Customize your transaction costs via `.env` variables:
- `COST_SCENARIO` (e.g. `BASE` or `CONSERVATIVE`)
- `COMMISSION_MODEL_TYPE`, `COMMISSION_BPS`, `COMMISSION_FLAT_FEE`, `COMMISSION_MINIMUM`
- `SLIPPAGE_MODEL_TYPE`, `FIXED_SLIPPAGE_BPS`, `MAX_SLIPPAGE_BPS`
- `SPREAD_MODEL_TYPE`, `HIGH_LIQUIDITY_SPREAD_BPS`, `LOW_LIQUIDITY_SPREAD_BPS`

### CLI Usage
Estimate costs before placing manual trades:
```bash
python -m bist_signal_bot costs estimate ASELS --side BUY --quantity 100 --price 50
python -m bist_signal_bot costs round-trip ASELS --side BUY --quantity 100 --entry-price 50 --exit-price 55
python -m bist_signal_bot costs scenarios
python -m bist_signal_bot costs config
```


## Phase 30: Risk Management Engine v1

The Risk Management Engine evaluates trading signals generated by strategies and transforms them into "Risk Decisions." The system acts as a protective layer prior to actual execution simulation.

### Key Capabilities
* **Position Sizing:** Methods include `FIXED_NOTIONAL`, `EQUITY_PERCENT`, `RISK_PERCENT`, `ATR_RISK`, `VOLATILITY_TARGET`, and `SCORE_WEIGHTED`. The default approach is `RISK_PERCENT`.
* **Stop Models:** Supports dynamic stop losses via `ATR_MULTIPLE`, `FIXED_PERCENT`, `RECENT_SWING`, or `VOLATILITY_BASED`.
* **Target Models:** Dynamic targets calculated using `RISK_REWARD_MULTIPLE`, `FIXED_PERCENT`, `ATR_MULTIPLE`, or `RECENT_RESISTANCE_SUPPORT`.
* **Risk Filters:** Protects portfolio with rules like max position size percent, maximum daily signals, maximum open positions, min R/R, and volatility / liquidity checks.

### Backtest Integration
The `BacktestEngine` can now intercept a `SignalCandidate`, ask the `RiskEngine` to evaluate it, and convert it into a simulated order **only if** the decision is `APPROVED`.
- Use `--use-risk-engine` flag in backtest CLI to enable this capability.

### Command Line Integration (CLI)
Evaluate individual signals using mock or local data directly through the risk interface:
```bash
python -m bist_signal_bot risk evaluate ASELS --source mock --strategy moving_average_trend
python -m bist_signal_bot risk size ASELS --side LONG --entry 50 --stop 47 --equity 100000
python -m bist_signal_bot risk stop-target ASELS --side LONG --entry 50 --method-stop FIXED_PERCENT --method-target RISK_REWARD_MULTIPLE
python -m bist_signal_bot risk config
```

### Important Disclaimers
* **Not Investment Advice:** The outputs are purely for research.
* **No Real Orders:** The system calculates abstract target positions. Real execution and order routing are deliberately out of scope for this architecture.
* **No Dashboards:** Execution is purely CLI or via testing modules.
* **Deterministic:** Calculations are entirely based on offline history.


### Phase 31: Portfolio Risk Engine
- **Portfolio vs Trade Risk**: Trade-level risk evaluates individual signals independently. Portfolio-level risk assesses how multiple signals affect the portfolio dynamically, ensuring capital boundaries and distribution limits are respected.
- **Exposure Management**: Controls Gross Exposure, Net Exposure, Max Sector Weight, and Max Symbol Weight.
- **Correlation Checks**: Cross-references new candidate signals against existing holdings. Limits overexposure to highly correlated assets. Correlation is derived from historical data and does not guarantee future relationships.
- **Allocation Strategies**: Implements multiple allocation models including `HYBRID`, `EQUAL_WEIGHT`, `SCORE_WEIGHTED`, `RISK_PARITY_SIMPLE`, `VOLATILITY_SCALED`, and `LIQUIDITY_WEIGHTED`.
- **Backtest Integration**: Portfolio logic is kept decoupled from backtest by default (`BACKTEST_USE_PORTFOLIO_RISK_ENGINE` disabled) so single-symbol runs still perform natively. Multi-symbol portfolio backtesting with these limits is reserved for advanced configurations.
- **No Real Orders**: `PortfolioRiskDecision` structures are strictly "Portfolio risk research outputs". They are NOT investment advice and no real orders are sent. The project adheres to strict restrictions against automated live trading, HTML scraping, and paid APIs.

## Phase 32: Paper Trading Motoru v1, Sanal Emir Defteri ve Simülasyon Katmanı

This phase introduces a robust Paper Trading Engine designed to simulate real market execution without ever placing real orders or putting real capital at risk. It acts as the execution simulator for signals validated by the Strategy Engine, Risk Engine, and Portfolio Risk Engine.

**Purpose & Guiding Principles:**
- **No Real Orders:** The Paper Trading Engine only produces a simulated ledger. Broker APIs are completely isolated, and no real-money orders are ever placed.
- **Local-First Ledger:** All paper trades, positions, fills, and ledger events are stored locally in atomic JSON files, preventing database dependencies.
- **Strict Verification:** Every order passes through trade-level and portfolio-level risk engines prior to a simulated "fill." Without risk approval, orders are rejected.
- **Deterministic Execution Modes:** Simulation executes deterministically against predefined conditions (e.g., `LATEST_CLOSE_RESEARCH`, `NEXT_OPEN_SIMULATED`, `MANUAL_PRICE`) to facilitate both research and CLI-driven workflow without look-ahead bias.
- **No Web Elements:** There are absolutely no web scraping techniques, Streamlit dashboards, HTML manipulation, or paid APIs included in this simulation layer.

**Core Data Models:**
- `PaperAccount`: Holds initial cash, current cash, equity, and realized/unrealized PnL.
- `PaperOrder`: The representation of an intent to buy/sell after risk checks. Includes metadata from the Strategy and Risk layers.
- `PaperFill`: Represents the simulated execution of a `PaperOrder`, heavily influenced by the `TransactionCostEngine` (commission, slippage, spread).
- `PaperPosition`: Summarizes active holdings and their mark-to-market values.
- `PaperLedgerState`: The aggregate state holding the account, orders, fills, positions, trades, and event history, saved as `ledger.json`.

**CLI Integrations:**
The new `paper` CLI commands provide comprehensive control over your simulation environment:
```bash
python -m bist_signal_bot paper init --account default --cash 100000
python -m bist_signal_bot paper status
python -m bist_signal_bot paper run-once ASELS --source mock --strategy moving_average_trend
python -m bist_signal_bot paper positions
python -m bist_signal_bot paper orders
python -m bist_signal_bot paper fills
python -m bist_signal_bot paper trades
python -m bist_signal_bot paper close ASELS --account default --source mock
python -m bist_signal_bot paper export --account default
python -m bist_signal_bot paper config
```

**Notifications & Audit:**
- Simulated runs can optionally be pushed to Telegram using `PAPER_SEND_TELEGRAM_SUMMARY`. All outputs strictly emphasize that the messages are for simulation/research purposes only and do not constitute investment advice.
- Complete audit trails (`PAPER_ACCOUNT_INITIALIZED`, `PAPER_FILL_SIMULATED`, etc.) are written sequentially to `audit.log` for debugging and back-verification.

## Phase 33: BIST Signal Scanner v1

Signal Scanner is a professional-grade component designed to scan symbols across the BIST universe, generate signals, run risk checks, evaluate portfolio allocations, rank, and summarize the top candidates.

### **Important Notes:**
- **Signal scan research output only. Not investment advice. No real order was sent.**
- **No HTML/web scraping** is performed.
- **No paid APIs** or services are used.
- **No real broker APIs** are called.
- The output of the scanner is solely for research and backtesting purposes.

### **Capabilities:**
- **Universe Modes**: Easily run scans on `symbols`, `watchlist`, `group`, or `all` active symbols.
- **Integration with Engines**: Leverages `StrategyEngine`, `RiskEngine`, and `PortfolioRiskEngine` to score and validate signals.
- **Ranking and Filtering**: Top candidates are ranked by `FINAL_SCORE` (or other sort keys), filtering out low confidence or high-risk signals.
- **Top N Candidates**: Truncates results to the Top N scoring candidates for concise reports.
- **Local Storage**: Automatically caches reports (JSON, CSV, Markdown) locally using `ScanReportStore`.
- **Telegram Notification**: Optional concise telegram summaries of the top candidates.
- **PaperTradingEngine**: Paper execution is disabled by default (`SCANNER_ALLOW_PAPER_EXECUTION=False`). It can be enabled strictly for simulation flows.
- **Error Isolation**: Built-in `continue_on_error` parameter to ensure one failing symbol does not break the entire scan batch.

### **CLI Usage:**
```bash
# Scan specific symbols
python -m bist_signal_bot scan symbols ASELS THYAO GARAN --source mock --strategy moving_average_trend

# Scan symbols and limit to top 5
python -m bist_signal_bot scan symbols ASELS THYAO GARAN --source mock --strategy breakout_volume --top 5

# Scan with custom sorting
python -m bist_signal_bot scan symbols ASELS THYAO GARAN --source mock --strategy moving_average_trend --sort FINAL_SCORE

# Scan and disable portfolio risk checks
python -m bist_signal_bot scan symbols ASELS THYAO GARAN --source mock --strategy moving_average_trend --no-portfolio-risk

# Output JSON
python -m bist_signal_bot scan symbols ASELS THYAO GARAN --source mock --strategy moving_average_trend --json

# Scan watchlist
python -m bist_signal_bot scan watchlist default --source mock --strategy moving_average_trend

# Scan watchlist and save reports
python -m bist_signal_bot scan watchlist default --source mock --strategy breakout_volume --save-report

# Scan a specific group
python -m bist_signal_bot scan group LIQUID --source mock --strategy moving_average_trend

# Scan all active symbols
python -m bist_signal_bot scan all --source mock --strategy moving_average_trend --top 20

# View recent scans
python -m bist_signal_bot scan recent

# View scanner config
python -m bist_signal_bot scan config
```

### Phase 34: Strategy Optimizer v1
- **Grid and Random Search**: Systematically test or randomly sample parameter combinations to find optimal settings using past data. Random search uses a deterministic seed for reproducibility.
- **Walk-Forward Optimization**: Automatically generate out-of-sample (OOS) testing windows, training parameters on past data and testing on forward data to reduce the risk of curve fitting. Provides parameter stability scores and overfit warnings.
- **Objective Metrics & Constraints**: Rank parameters by Total Return, Sharpe, Sortino, Calmar, Profit Factor, Max Drawdown, or a customizable Composite Score. Exclude parameter sets that fall below minimum trade counts, exceed max drawdown thresholds, or fail to achieve positive returns.
- **Robustness**: Does not mutate original dataframes, enforces offline-only tests, restricts huge grid limits, and exports reports into JSON/CSV/Markdown natively.
- **Important Disclaimer**: Optimizer output is solely for past-data research. Past optimized parameters do not guarantee future results. This module does not provide investment advice, does not use a broker API, sends no real orders, uses no paid services, and does not provide HTML dashboards or web scraping.

### Phase 34: Strategy Optimizer v1
- **Grid and Random Search**: Systematically test or randomly sample parameter combinations to find optimal settings using past data. Random search uses a deterministic seed for reproducibility.
- **Walk-Forward Optimization**: Automatically generate out-of-sample (OOS) testing windows, training parameters on past data and testing on forward data to reduce the risk of curve fitting. Provides parameter stability scores and overfit warnings.
- **Objective Metrics & Constraints**: Rank parameters by Total Return, Sharpe, Sortino, Calmar, Profit Factor, Max Drawdown, or a customizable Composite Score. Exclude parameter sets that fall below minimum trade counts, exceed max drawdown thresholds, or fail to achieve positive returns.
- **Robustness**: Does not mutate original dataframes, enforces offline-only tests, restricts huge grid limits, and exports reports into JSON/CSV/Markdown natively.
- **Important Disclaimer**: Optimizer output is solely for past-data research. Past optimized parameters do not guarantee future results. This module does not provide investment advice, does not use a broker API, sends no real orders, uses no paid services, and does not provide HTML dashboards or web scraping.
