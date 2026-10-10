# Windows'ta 7/24 calistirma (forward shadow + runtime)

Bu proje arastirma ve paper simulation amaclidir. Gercek emir gondermez. (No real order sent.)

1. Task Scheduler (onerilen, en saglam): gorev "Forward Shadow Daily", tetikleyici Pzt-Cum 19:30 (Istanbul saati) ve ikinci
   gorev 08:30 (catch-up). Eylem: `C:\Projelerim\gptbist\.venv\Scripts\python.exe -m bist_signal_bot forward run-daily`,
   "Start in" = repo koku. Ayarlar: "Run task as soon as possible after a scheduled start is missed" ACIK, "Wake the computer" ACIK,
   bilgisayar uyku modunda olmamali (Power Options -> Never sleep). Is idempotent oldugu icin tekrar kosmak zararsizdir.
   Saglik icin ek gorev 19:50: `... forward health --dry-run` (Telegram icin `--notify`; `TELEGRAM_DRY_RUN` degerine uyar).
2. Runtime dongusu ayri: `python -m bist_signal_bot runtime loop` (RUNTIME_MAX_ITERATIONS / RUNTIME_SLEEP_SECONDS) - istege bagli.
3. Dahili scheduler: `python -m bist_signal_bot scheduler defaults --create --confirm` forward isleri (19:30 + 08:30,
   islem gunleri) ekler; `scheduler run-due --confirm` dakikada bir cagrilmalidir (tetikleyici 5 dk tolerans verir) - Task
   Scheduler yolu daha guvenilirdir.
4. Kontrol: `forward health` -> kill switch, zincir dogrulama, veri tazeligi, disk. `data/forward/alerts.jsonl` izlenir.
5. Yedek: `data/forward/` dizinini duzenli kopyalayin (decisions/outcomes zincirleri kanit niteligindedir; silmeyin/duzenlemeyin).
