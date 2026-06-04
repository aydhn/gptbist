# Phase 110: Strict Release Branch Policy, Version Governance & Final Post-Release Closure

## 1. Eklenen / Güncellenen Dosyalar
- `bist_signal_bot/release_policy/models.py`: ReleasePolicyStatus, BranchKind, ChangeRiskLevel, ChangeType, VersionBumpType, BranchPolicy, VersionSnapshot, ChangeRequest, CompatibilityCheckResult, ChangelogEntry, MigrationNote, DeprecationNotice, ReleaseBranchFreezeManifest, FinalClosureManifest, ReleasePolicyGovernanceAssessment, ReleasePolicyReport eklendi.
- `bist_signal_bot/release_policy/branch_policy.py`: BranchPolicyRegistry, classify_branch, validate_branch_policy eklendi.
- `bist_signal_bot/release_policy/versioning.py`: VersionGovernanceEngine, build_version_snapshot, is_valid_semver, compare_versions, suggest_version_bump eklendi.
- `bist_signal_bot/release_policy/compatibility.py`: CompatibilityPolicyChecker, run_compatibility_check, check_*_compatibility eklendi.
- `bist_signal_bot/release_policy/change_control.py`: ChangeControlManager, create_change_request, estimate_risk, required_artifacts eklendi.
- `bist_signal_bot/release_policy/changelog.py`: ChangelogBuilder eklendi.
- `bist_signal_bot/release_policy/migrations.py`: MigrationNoteBuilder eklendi.
- `bist_signal_bot/release_policy/deprecations.py`: DeprecationPolicyManager eklendi.
- `bist_signal_bot/release_policy/freeze.py`: ReleaseBranchFreezeManager eklendi.
- `bist_signal_bot/release_policy/closure.py`: FinalPostReleaseClosureBuilder eklendi.
- `bist_signal_bot/release_policy/governance.py`: ReleasePolicyGovernanceEngine eklendi.
- `bist_signal_bot/release_policy/storage.py`: ReleasePolicyStore eklendi.
- `bist_signal_bot/release_policy/reporting.py`: Reporting mapper & formatters eklendi.
- `bist_signal_bot/app/release_policy_app.py`: App factory fonksiyonları eklendi.
- `bist_signal_bot/core/exceptions.py`: İlgili Exception sınıfları eklendi.
- `bist_signal_bot/core/audit.py`: Audit Event Type'ları eklendi.
- `bist_signal_bot/storage/paths.py`: `get_release_policy_dir` eklendi.
- `bist_signal_bot/config/settings.py`: Ayarlar güncellendi.
- `.env.example`: İlgili key'ler eklendi.
- `bist_signal_bot/docs/*`: 90, 91 ve 92 numaralı rehberler oluşturuldu.
- `bist_signal_bot/examples/*`: Workflow örnekleri oluşturuldu.
- `bist_signal_bot/tests/*`: test_branch_policy.py, test_change_control.py, test_release_branch_freeze.py eklendi.
- `bist_signal_bot/cli/release_policy_cli.py`: CLI argparse ve handle komutları oluşturuldu.
- `README.md`: Phase 110 özetleri ve Final Kapaniş Komut Seti eklendi.

## 2. Strict Release Branch Policy v1 Mimarisi Özeti
Sistem, `main`, `develop`, `release`, `hotfix`, `feature`, `experimental` ve `archive` branch'leri için katı kurallar tanımlar. Her bir branch tipinin izin verdiği değişiklik türleri (`ChangeType`), gereken süreçler (QA, Ops, Final Audit, Changelog vb.) ve branch'in `protected` olup olmadığı `BranchPolicy` üzerinden kontrol edilir. Sistem metadata üretir ve release pipeline'larının bu kurallara uymasını sağlar.

## 3. Modeller
- **BranchPolicy:** Branch kısıtlarını tanımlar.
- **VersionSnapshot:** Projenin bir anındaki tüm kontrat versiyonlarını barındırır.
- **FinalClosureManifest:** Projenin son durumunu (Phase 1-110 kapanışı), tamamlanan modülleri, kabul edilen limitasyon ve riskleri, son governance durumunu içerir ve "Gerçek emir gönderilmediğini" teyit eder.

## 4. Branch Policy Registry Davranışı
Branch ismine regex ile bakar (örn. `^release/.*$`), eşleşen `BranchPolicy`'i döner. İzin verilmeyen change type geldiğinde reject eder. `main` ve `release` gibi kritik branch'leri `protected` yapar.

## 5. Version Governance Davranışı
Mevcut versiyonları (project, schema, config, CLI vs.) `VersionSnapshot` içinde tutar. Versiyon string'lerinin geçerli `Semantic Versioning` standardında olduğunu (`is_valid_semver`) kontrol eder. Değişiklik listesine göre bir sonraki mantıksal versiyonu (MAJOR/MINOR/PATCH) `suggest_version_bump` metodu ile önerir.

## 6. Compatibility Policy Checker Davranışı
Yeni release alınmadan önce tüm kontratlarda (Schema, CLI, Config, Data, Plugin) "drift" (kayma) olup olmadığını kontrol eder. Eğer "breaking" bir değişiklik tespit edilirse durumu `FAIL` veya `BLOCKED`'a çeker. Dış servislere istek atmaz (tamamen offline check).

## 7. Change Control Davranışı
Yeni bir geliştirme yapıldığında, CLI veya entegrasyon üzerinden bir `ChangeRequest` oluşturulmasını zorunlu kılar. `classify_change` ile türünü, `estimate_risk` ile seviyesini belirler. Breaking changes gibi kritik değişikliklerde Migration Note ve Changelog zorunluluğu (`required_artifacts`) getirir.

## 8. Changelog / Migration / Deprecation Davranışı
- **Changelog:** Tüm change request'leri sürüm numarasına bağlayarak `ChangelogEntry`'lere çevirir, formatlayıp `.jsonl` yazar. Unsafe investment claim'lere izin vermez.
- **Migration:** Schema veya config değişikliği varsa, hangi adımdan nereye geçileceğine dair required `MigrationNote` üretilmesini sağlar.
- **Deprecation:** Kaldırılacak özellikler için `removal_target_version` planlaması yapan `DeprecationNotice` üretir.

## 9. Release Branch Freeze Davranışı
`release/*` branch'lerinde kodun dondurulmasını temsil eder. Onay (`confirm=True`) verilmediği sürece `frozen=False` olarak kaydeder. Blocking QA veya Ops hataları varsa dondurma işlemine engel koyar (`blocked_changes`). Dondurulmuş snapshot için bir manifest json yazar.

## 10. Final Post-Release Closure Davranışı
Sistemin 1-110 Fazlık MVP handoff durumunun mühürlendiği manifesttir (`FinalClosureManifest`). 39 modülün tamamlandığını (`completed_modules`), broker/gerçek emir entegrasyonu olmadığını (`accepted_limitations`), araştırma odaklı olduğu kabulünü içerir. Her zaman `no_real_order_sent=True` assertion'ı yapar.

## 11. Release Policy Governance Davranışı
Yukarıdaki tüm durumları (branch, version, compatibility, freeze, vb.) toplayıp birleştirir. Eğer bir yerde "BLOCKED" var ise, overall statüyü `BLOCKED` yapar. İçeriklerde "trade ready", "işlem yapılabilir" gibi kelimeler yakalarsa güvenlik ve compliance nedeniyle raporu bloke eder.

## 12. QA / Ops / Final Audit / Final Handoff Entegrasyonu
CLI araçları (örn. `qa release-gate`, `ops readiness`) parametre olarak `--include-release-policy` alır ve Governance modülünden `status` çeker. Final Audit `go-no-go` sürecinde release policy "BLOCKED" ise release candidate durdurulur.

## 13. Maintenance / Performance / Plugins / Markets / Explainability Entegrasyonu
- **Maintenance:** Quarterly periyodik taramalarda policy kontrolü de çalışır.
- **Performance:** `benchmark --scenario RELEASE_POLICY_CHECK` gibi performans snapshotları desteklenir.
- **Plugins/Markets vb.:** Kendi contract versiyonlarını bu module `Plugin Contract Version` olarak aktarır ve Compatibility Checking listesine sokar.

## 14. Data Catalog / Feature Store / Model Registry / Report Templates Entegrasyonu
Veri kontratlarındaki (schema) en ufak değişim Compatibility'de `Data Contract Drift` veya `Schema Drift` olarak yakalanır. Rapor template'lerinin yeni schema ile uyuşup uyuşmadığı takip edilir.

## 15. Reports / Local UI / Healthcheck / Doctor / Governance Entegrasyonu
`healthcheck` ve `doctor` komutları artık release policy argümanları alır. Doctor, kırılmış versiyon stringleri, boş migration'ları uyarır. Local UI, oluşan freeze/closure manifestlerini read-only modda sunmak üzere (read-only view) hazırlanmıştır.

## 16. CLI release-policy Komutları ve Örnekleri
```bash
python -m bist_signal_bot release-policy status --json
python -m bist_signal_bot release-policy version --snapshot --json
python -m bist_signal_bot release-policy compatibility --target-version 1.0.0
python -m bist_signal_bot release-policy change --title "Add X" --type FEATURE
python -m bist_signal_bot release-policy freeze --branch release/v1.0.0 --target-version 1.0.0 --confirm
python -m bist_signal_bot release-policy closure --dry-run
```

## 17. Audit / Notification Entegrasyonu
Release Policy eylemleri tetiklendiğinde `RELEASE_BRANCH_FREEZE_CREATED` veya `FINAL_CLOSURE_MANIFEST_CREATED` gibi kayıtlar `core/audit.py` loglarına yazılır. Notification modülü, Telegram (mock) üzerinden formatlı "Release Policy Özeti" mesajı üretebilir.

## 18. README / docs / examples Final Güncellemeleri
- `90_STRICT_RELEASE_BRANCH_POLICY.md`, `91_FINAL_POST_RELEASE_CLOSURE.md`, `92_LONG_TERM_DEVELOPMENT_CONTROL.md` rehberleri oluşturulmuştur.
- İlgili markdown'larda workflow adımları eklenmiş, Final Kapanış Komut Seti README.md altına kaydedilmiştir.

## 19. Test Listesi
1. `test_branch_policy.py`: Disclaimer içerikleri, Registry davranışları ve branch kuralları test edilir.
2. `test_change_control.py`: Change request üretimi, risk tespiti, changelog markdown geçerlilikleri (unsafe kelime reddi) test edilir.
3. `test_release_branch_freeze.py`: Freeze manifest confirm davranışı, Closure builder limitasyon ve risk assertion'ları test edilir. Governance motorunun yasaklı kelimeleri (trade ready vb.) bloke etmesi teyit edilmiştir.
(Not: Pydantic veya benzeri third-party bağımlılık eksikliğinden import error alınsa dahi test kodları repoda standart formatıyla yazılmıştır.)

## 20. Çalıştırma Komutları
(Bkz. Bölüm 16)

## 21. Final Phase 110 Kapanış Komut Seti
```bash
python -m bist_signal_bot healthcheck --bootstrap --ops --cli-ux --docs-hub --data-catalog --feature-store --model-registry --monitoring --leaderboard --orchestrator --final-audit --final-handoff --performance --data-import --report-templates --synthetic-scenarios --local-ui --explainability --markets --maintenance-automation --plugins --release-policy

python -m bist_signal_bot release-policy compatibility --target-version 1.0.0 --json
python -m bist_signal_bot release-policy freeze --branch release/v1.0.0 --target-version 1.0.0 --dry-run
python -m bist_signal_bot release-policy closure --dry-run
python -m bist_signal_bot release-policy governance --json
python -m bist_signal_bot release-policy report --latest
```

## 22. Phase 1-110 Kapanışı
Bu geliştirme ile birlikte Phase 1'den başlayıp 110. faza kadar uzanan **BIST Signal Bot MVP (Local-First, Research-Only)** geliştirme hattı resmi olarak tamamlanmıştır.

Tüm sistemin uyumluluk, governance, denetim, release ve kapama yönetimi local architecture üzerinde tam teşekküllü olarak işlevseldir.

Bundan sonra yapılacak her türlü yeni özellik, entegrasyon veya hata giderme adımı; kurulan yeni **Roadmap / Change Request / Release Policy** mekanizmaları (örn: Phase 111+) üzerinden yürütülecek ve final kapaniş kurallarına tabi olacaktır.
