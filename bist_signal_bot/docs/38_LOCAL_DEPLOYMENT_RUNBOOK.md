# Local Deployment Runbook

## İlk Kurulum Checklist
- Ortam değişkenlerini oluştur.
- Deployment Doctor çalıştır.
- Klasörleri başlat.
- `deploy first-run` çalıştır.

## İlk Gün Yapılacaklar
- Smoke testlerin sorunsuz geçtiğinden emin ol.
- Config ve profilleri gözden geçir.

## Günlük Rutin
- Sistem sağlığı için `healthcheck` çalıştır.
- Sinyal durumunu kontrol et.

## Haftalık Rutin
- Bakım işlemleri.

## Backup ve Maintenance
- `maintenance doctor` kullan.

## Governance Kontrol
- `governance policy` ile kuralları incele.

## Safe Scheduler
- `scheduler` dry-run modunda izle.

## Telegram Dry-Run
- Test gönderimleri izle.

## Recovery
- `deploy first-run` ile yapılandırmayı onar.
