# Local Scheduler (Phase 65)

## Mimari
BIST Signal Bot, local-first çalıştığı için harici bir cron/scheduler servisinden (Celery, Redis) bağımsız olarak kendi `scheduler` katmanına sahiptir. Bu katman `run-due` mantığıyla çalışır, yani sistem saatine göre zamanı gelmiş işleri bulur ve çalıştırır. Harici bir sistem (örn. crontab, Windows Task Scheduler) periyodik olarak `scheduler run-due` komutunu tetikleyebilir.

## Modüller
- `calendar.py`: BIST resmi tatilleri, yarım günler ve hafta sonlarını anlar. Web kazımaz, `data/scheduler/calendar/bist_holidays.csv` dosyasına bakar.
- `session.py`: BIST seans durumlarını (PRE_MARKET, OPENING, INTRADAY, vb.) bilir.
- `triggers.py`: Bir job'un due (zamanı gelmiş) olup olmadığını kontrol eder.
- `locks.py` ve `deduplication.py`: Aynı işin 2 kere çalışmasını engeller, global kilit koyar.

## Güvenlik & Prensipler
- **Asla emir göndermez:** Scheduler'in hiçbir işi (job) gerçek bir borsa emri üretmez. Tamamen "research-only" çalışır.
- **Dry-run varsayılanı:** Kritik işler varsayılan olarak dry-run çalışır.
- **Destructive işler engellidir:** Backup silme veya migrate gibi işler schedule edilemez.

## CLI Komutları
- `python -m bist_signal_bot scheduler defaults --create --confirm` (varsayılan bakım işlerini kurar)
- `python -m bist_signal_bot scheduler run-due --dry-run` (çalışması gereken işleri simüle eder)
- `python -m bist_signal_bot scheduler list`
