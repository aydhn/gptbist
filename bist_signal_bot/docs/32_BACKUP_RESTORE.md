# Local Backup & Restore, Data Hygiene, Migration Katmanı

BIST Signal Bot, MVP seviyesinde local-first veri prensibi ile çalışır. Data klasörü altında raporlar, sinyaller, cache, loglar, portfolio, stress, drift gibi pek çok alt dizin biriktirir.

Bu katman, data klasörünün güvenli şekilde yedeklenmesi, zararlı dosyaların engellenmesi, retention prensipleri ile eski verilerin silinmesi (cleanup), schema sürümlerinin uyumluluğu (migration) ve sağlık kontrolü (doctor) için `maintenance` adı altında tasarlanmıştır.

## Özellikler

- **Dry-run First:** Restore ve Cleanup gibi "destructive" (yok edici) işlemler varsayılan olarak dry-run çalışır. Gerçek işlem için explicit `confirm` gereklidir.
- **Secret Exclusion:** `.env`, `.pem`, token, password ve secret dosyaları `ALL_SAFE` scope ile alınan backuplara asla dahil edilmez. Manifest dosyasına *excluded* sebebi ile yazılır.
- **Checksum Verification:** Backup sonrası oluşturulan arşiv ve manifest üzerindeki hash (SHA-256) bilgileri tutarlılık kontrolünden geçirilebilir.
- **Path Traversal Protection:** Restore işlemi, arşiv içerisindeki `../` veya absolute path (tam yol) kullanan dosya adlarını reddeder.
- **Offline / Local Only:** Cloud yüklemesi, broker bağlantısı, dış servis kullanımı veya web arayüzü yoktur. Her şey yerel diskte çalışır.

## Kullanım

Maintenance işlemleri `bist_signal_bot.cli.maintenance` veya ana modül üzerinden tetiklenebilir:

### Backup Almak
```bash
# Sadece dry-run yap, hangi dosyaların yedekleneceğini gör
python -m bist_signal_bot.cli.maintenance backup-create --dry-run

# Tüm safe scope dosyaları yedekle ve verify et
python -m bist_signal_bot.cli.maintenance backup-create --verify
```

### Restore Etmek
```bash
# Restore dry-run (planı gösterir)
python -m bist_signal_bot.cli.maintenance restore --backup data/maintenance/backups/20240101_120000/backup.zip

# Gerçek restore işlemi
python -m bist_signal_bot.cli.maintenance restore --backup data/maintenance/backups/20240101_120000/backup.zip --confirm
```

### Doctor (Sağlık Kontrolü)
```bash
python -m bist_signal_bot.cli.maintenance doctor
```

## Disclaimer
Maintenance modülleri; **yatırım tavsiyesi vermez, trade yapmaz, gerçek emir oluşturmaz.** Çıktılar operasyonel metadata amaçlıdır.
