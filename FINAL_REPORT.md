# Phase 90 - Local MVP Packaging ve Bootstrap V1 Tamamlandı

Local MVP Packaging ve Bootstrap mimarisi başarıyla entegre edildi. Proje artık yerel bir makinede çalıştırılmaya, test edilmeye ve araştırma amaçlı kullanılmaya hazır hale getirildi.

## 1. Eklenen ve Güncellenen Dosyalar
- `bist_signal_bot/bootstrap/models.py` (Modeller)
- `bist_signal_bot/bootstrap/profiles.py` (RunProfileRegistry)
- `bist_signal_bot/bootstrap/initializer.py` (BootstrapInitializer)
- `bist_signal_bot/bootstrap/validator.py` (BootstrapValidator)
- `bist_signal_bot/bootstrap/demo.py` (OfflineDemoRunner)
- `bist_signal_bot/bootstrap/recipes.py` (CommandRecipeRegistry)
- `bist_signal_bot/bootstrap/release_bundle.py` (ReleaseBundleBuilder)
- `bist_signal_bot/bootstrap/onboarding.py` (OnboardingGuideBuilder)
- `bist_signal_bot/bootstrap/storage.py` (BootstrapStore)
- `bist_signal_bot/bootstrap/reporting.py` (Raporlama Metotları)
- `bist_signal_bot/app/bootstrap_app.py` (App Factory)
- `bist_signal_bot/cli/bootstrap_cli.py` (Alt Komut Yöneticisi)
- `bist_signal_bot/cli/commands.py` (Ana CLI Modülü, Güncellendi)
- `bist_signal_bot/config/settings.py` (Ayar Eklentileri)
- `bist_signal_bot/core/audit.py` (Denetim Olayları)
- `bist_signal_bot/core/exceptions.py` (Özel Hata Sınıfları)
- `bist_signal_bot/storage/paths.py` (Bootstrap dizin desteği)
- `bist_signal_bot/tests/test_bootstrap.py` (İnternetsiz Birim Testler)
- `README.md` (Özet Güncellemeler)
- `bist_signal_bot/docs/` (Kılavuzlar ve Örnek Çalışmalar eklendi)

## 2. Local MVP Packaging / Bootstrap V1 Mimarisi Özeti
Sistem, gerçek emir ve piyasa çağrılarını varsayılan olarak izole eden `research-only` tabanlı, çevrimdışı, kendi kendine doğrulanan bir bootstrap yapısına kavuştu.

## 3. RunProfile / BootstrapValidationResult / ReleaseBundleManifest Modelleri Özeti
- `RunProfile`: Kullanıcıların sistemin hangi modüllerini çalıştıracağını ayarlayan metadata yapısı. (Örn: MINIMAL, STANDARD, DEMO)
- `BootstrapValidationResult`: Ortam ve yapılandırma denetimlerinin (Python versiyonu, paket importları, güvenlik profili vb.) birleşik sonucunu tutar.
- `ReleaseBundleManifest`: Dağıtıma hazır paketin meta verisini ve özet durumunu taşır (Dahili modüller, checksum, versiyon vd.).

## 4. Run Profile Registry Davranışı
MINIMAL, STANDARD, FULL_RESEARCH, QA, DEMO, SAFE_MAINTENANCE olmak üzere 6 varsayılan profil desteklenir. Canlı işlem parametreleri engellenir (BLOCK/WATCH) ve hepsi "research-only" disclaimer içerir.

## 5. Bootstrap Initializer Davranışı
Varsayılan durumda veri ve konfigürasyon (örneğin `.env.example`, `data/`) dizinlerini yaratır. "Confirm" onayı ve "Dry-Run" (varsayılan) seçeneğiyle zararlı ezmelerden kaçınır.

## 6. Bootstrap Validator Davranışı
Geçerli bir araştırma paketi oluşturulabilmesi için Python sürümünü (3.10+), kütüphane gereksinimlerini, veri dizinlerinin yazılabilirliğini, güvenlik bildirimlerini denetler.

## 7. Offline Demo Runner Davranışı
İnternetsiz sentetik test veri setiyle örnek bir tarama, filtreleme, inceleme ve portföy operasyonu serisini (QA, Review, Scan vd.) çalıştırır ve sanal çıktıları raporlar.

## 8. Command Recipe Registry Davranışı
Quickstart başta olmak üzere "minimal scan", "context", "portfolio", "ops health" vs. için en sık kullanılan komut reçetelerini barındırır. Markdown uyumlu çıktılar üretir.

## 9. Release Bundle Builder Davranışı
Uygulamanın çalışır haldeki bileşenlerinin, checksum ve referans paketi tanımlarının olduğu manifest paketini oluşturur.

## 10. Onboarding Guide Davranışı
Kullanıcıya uygulamaya "hoş geldin" mesajı ve hızlı başlama talimatlarını sağlayan metin tabanlı Markdown yönergeleri sunar.

## 11. Healthcheck / Doctor / QA / Ops Entegrasyonu
- `healthcheck` ve `doctor` alt komutları `--bootstrap` bayrağı ile bootstrap konfigürasyonunu, çalışma profilini ve sentetik kurulum onaylarını özetler.
- QA Release Gate `--include-bootstrap` flagi ile bootstrap çıktılarını doğrulama zincirine entegre eder.
- Ops Readiness, mevcut yapılandırmanın sağlıklı önyükleme onayı alıp almadığını `--include-bootstrap` ile sunar.

## 12. Runtime / Reports / Research Ledger / Knowledge Entegrasyonu
- `Runtime` ayarları, aktif RunProfile referansına sahiptir. Unsafe profile kullanımına dair raporlara uyarı ekler.
- `Reports (Daily vb.)`, günlük rapora seçili çalışma profilini (active profile), son demo sürüm sonucunu ekleme yeteneğine kavuştu.

## 13. Governance / Security / Notifications Entegrasyonu
Çıktı ve profillere uygulanan PathGuard kullanımı, ClaimsGuard sansürü ("al/sat", "yatırım", "garanti", vb.) etkin kılındı. Ayrıca profil "canlı emir" veya "aracı kurum API" aktifleştirmesi teşebbüslerini Blok listesine ekler.

## 14. CLI Bootstrap Komutları
- `python -m bist_signal_bot bootstrap profiles`
- `python -m bist_signal_bot bootstrap init --confirm`
- `python -m bist_signal_bot bootstrap validate`
- `python -m bist_signal_bot bootstrap demo`
- `python -m bist_signal_bot bootstrap recipes show QUICKSTART`
- `python -m bist_signal_bot bootstrap release-bundle`

## 15. Audit Entegrasyonu
`core/audit.py` üzerinde yeni AuditEventType'lar (BOOTSTRAP_PROFILE_SELECTED, BOOTSTRAP_INIT_COMPLETED, OFFLINE_DEMO_RUN vs.) desteklenir duruma getirildi.

## 16. Docs ve Örnek Workflow Güncellemeleri
Yeni başlayanlar için `00_QUICKSTART.md`, `01_LOCAL_INSTALL.md` ile komut referansları (`04_COMMAND_RECIPES.md` vb.) proje içerisine dahil edilerek paketlendi.

## 17. Test Listesi
İlgili testler `pytest bist_signal_bot/tests/test_bootstrap.py` adresinde bulunmaktadır:
1. `test_registry_unsafe_override` (Geçersiz profil önlemi)
2. `test_registry_defaults` (Sıfır profiller listesi)
3. `test_initializer_dry_run` (Eksik onay simülasyonu)
4. `test_initializer_confirm` (Klasör oluşturma)
5. `test_validator_paths`
6. `test_demo_runner` (Sanal sistem koşturucu)
7. `test_recipes` (Komut listeleri ve çıktı testleri)
8. `test_release_bundle`
9. `test_onboarding` (Kılavuzlar)
10. `test_storage` (Model yazma ve JSONL çevirisi denetimleri)

## 18. Çalıştırma Komutları
Tüm eklemelerin çalıştığından emin olmak için:
```bash
python -m bist_signal_bot bootstrap profiles
python -m bist_signal_bot bootstrap validate
python -m bist_signal_bot bootstrap demo
python -m bist_signal_bot bootstrap recipes
python -m pytest bist_signal_bot/tests/test_bootstrap.py
```

## Kapanış
Mimari sorunsuz entegre edildi. Mevcut proje modülleri bozulmadan (strict-safeguard) Phase 90 tamamlandı. Uygulama lokal düzeyde bir MVP Package Release yapısına sahiptir. Phase 91'e hazırız!
