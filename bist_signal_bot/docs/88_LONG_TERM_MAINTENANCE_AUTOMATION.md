# Phase 108: Long-Term Maintenance Automation

## Mimari
Maintenance Automation katmanı, BIST Signal Bot'un yerel ve güvenli bakım operasyonlarını otomatize eder.
Bu katman; local dosya sistemi, storage JSONL dosyaları ve loglar üzerinde rotation, cleanup, ve policy check görevlerini üstlenir.

## Cadence Policies
Sistem `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, ve `ON_DEMAND` bakım planlarına (cadence) sahiptir.

## Maintenance Actions
Belirli görevler `HEALTHCHECK`, `DOCTOR`, `CACHE_CLEANUP`, vb. şeklinde tanımlanır ve registry üzerinden planlanır.

## Dry-run and Confirm
Tüm `destructive` (silme, arşivleme) işlemleri varsayılan olarak `dry-run=True` modunda çalışır ve gerçek işlem için `--confirm` flag'ine ihtiyaç duyar.

## Cleanup and Retention
Dosyaların türüne göre (CACHE, REPORT, LOG vs.) sistemde bir tutma süresi (retention days) belirlenmiştir. Bu süreyi aşan dosyalar CleanupCandidates olarak toplanır.

## Rotation
Logların ve reportların eski olanlarının ziplenmesi veya silinmesi sağlanır.

## Backup Manifest
`backup.py`, önemli dosyaların SHA-256 hash'ini alarak `BackupManifest` modeli oluşturur, broker backup aracı değildir.

## Staleness Detection
Stale kalmış jobları, eksik raporları, bozuk cachi tespit eder.

## Orchestrator, QA, Ops Integration
Sistem Orchestrator üzerinden scheduled bakım run'ları oluşturabilir ve QA/Ops gate'lerine entegre edilmiştir.

## Güvenli Dil Kuralları (Safe Language)
Bakım aracı sadece "Yerel yazılım bakımı" yaptığını iddia eder, kesinlikle trade success, broker update veya "deployment ready" tarzı claim'lerde bulunmaz.

## Troubleshooting
Eğer `MaintenanceAutomationError` alırsanız logs dizinini inceleyiniz ve `doctor` komutu ile kontrol sağlayınız.
