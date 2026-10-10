# Windows Gorev Zamanlayici (schtasks) - SADECE DOKUMANTASYON

> **ISTEGE BAGLI - KULLANICI ISTEMIYOR.** Kullanici otomatik calistirma istemiyor; tum gunluk/haftalik isler ELLE komutla
> kosulur (bkz. daily_forward_runbook.md). Bu belge yalnizca referanstir; hicbir sey otomatiklestirilmez ve gorev olusturulmaz.

Bu proje arastirma ve paper simulation amaclidir. Yatirim tavsiyesi degildir. Gercek emir gondermez. (No real order sent.)

> UYARI: Bu belgedeki komutlar METIN olarak verilmistir; hicbiri otomatik calistirilmaz ve bu repo isletim sistemi
> gorevi OLUSTURMAZ. Komutlari yalnizca siz, yonetici olmayan (kendi kullanici) bir PowerShell/cmd penceresinde, okuyarak
> calistirin. Bilgisayar gorev saatlerinde ACIK ve UYANIK olmalidir (Power Options -> Never sleep). Kapaliysa gorev
> kosmaz; "forward run-daily" idempotent oldugu icin gec calistirmak zararsizdir, kacan gunler ise kayitta eksik kalir
> (geriye donuk doldurulmaz).

Varsayimlar: repo `C:\Projelerim\gptbist`, Python `C:\Projelerim\gptbist\.venv\Scripts\python.exe`, saatler yerel saat
(Europe/Istanbul). Seans kapanisi 18:00, gunluk bar hazir olma suresi `FORWARD_SESSION_READY_TIME` (18:30).
Tum gorevler hafta ici (MON-FRI); haftalik gorev pazar gunudur. Her komut `cmd /c "cd /d ... && ..."` ile repo kokunden
calisir ve ciktiyi `logs\sched_*.log` dosyasina ekler (`logs` dizini yoksa once olusturun: `mkdir C:\Projelerim\gptbist\logs`).

## 1. Gunluk veri guncelleme - 18:45

```
schtasks /Create /TN "BIST\DailyArchiveUpdate" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 18:45 /RL LIMITED /F /TR "cmd /c cd /d C:\Projelerim\gptbist && .venv\Scripts\python.exe -m bist_signal_bot daily archive-update --all-active >> logs\sched_archive.log 2>&1"
```

## 2. Forward run-daily + makbuz - 18:50

```
schtasks /Create /TN "BIST\ForwardRunDaily" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 18:50 /RL LIMITED /F /TR "cmd /c cd /d C:\Projelerim\gptbist && .venv\Scripts\python.exe -m bist_signal_bot forward run-daily --receipt >> logs\sched_forward.log 2>&1"
```

## 3. Saglik raporu - 19:10

```
schtasks /Create /TN "BIST\ForwardHealth" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 19:10 /RL LIMITED /F /TR "cmd /c cd /d C:\Projelerim\gptbist && .venv\Scripts\python.exe -m bist_signal_bot forward health --dry-run >> logs\sched_health.log 2>&1"
```

(Telegram icin `--dry-run` yerine `--notify`; `TELEGRAM_DRY_RUN` ayarina uyar.)

## 4. Haftalik yeniden egitim - Pazar 10:00

Model egitimi hicbir zaman otomatik "champion" yapmaz; terfi icin ayrica `model-loop promote ... --confirm` gerekir.

```
schtasks /Create /TN "BIST\WeeklyRetrain" /SC WEEKLY /D SUN /ST 10:00 /RL LIMITED /F /TR "cmd /c cd /d C:\Projelerim\gptbist && .venv\Scripts\python.exe -m bist_signal_bot model-loop daily-train --only-if-due >> logs\sched_retrain.log 2>&1"
```

## 5. Gunluk yedek + butunluk - 19:20

Butunluk kontrolu once calisir; FAIL ise yedek yine alinir ama gorev sonucu hatali kalir (uyari icin bkz. gunluk runbook).

```
schtasks /Create /TN "BIST\ForwardIntegrityBackup" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 19:20 /RL LIMITED /F /TR "cmd /c cd /d C:\Projelerim\gptbist && .venv\Scripts\python.exe -m bist_signal_bot forward integrity >> logs\sched_integrity.log 2>&1 & .venv\Scripts\python.exe -m bist_signal_bot forward backup >> logs\sched_backup.log 2>&1"
```

Yedekler `data\backups\forward\forward_backup_YYYYMMDD_HHMMSS.zip` olarak yazilir; son `FORWARD_BACKUP_KEEP` (varsayilan 14)
adet tutulur, yalnizca bu aracin urettigi eski zip'ler silinir. `.env` ve sirlar ASLA yedege girmez. Yedegi baska bir diske /
buluta MANUEL kopyalayin (`forward backup --dest D:\yedek\bist`).

## Yonetim (isteğe bagli, yine metin)

```
schtasks /Query /TN "BIST\ForwardRunDaily" /V /FO LIST
schtasks /Run /TN "BIST\ForwardRunDaily"
schtasks /Delete /TN "BIST\ForwardRunDaily" /F
```

Kacan gorevler icin Gorev Zamanlayici arayuzunde "Zamanlanmis baslangic kacirilirsa gorevi en kisa surede calistir"
secenegini acin (komut satirindan `/Create` bunu varsayilan olarak kapali birakir). Sira ve uyarilar icin
`docs/runbooks/daily_forward_runbook.md`.
