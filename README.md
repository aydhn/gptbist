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
