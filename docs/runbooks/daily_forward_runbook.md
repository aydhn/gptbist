# Gunluk Forward Runbook

Bu proje arastirma ve paper simulation amaclidir. Yatirim tavsiyesi degildir. Gercek emir gondermez. (No real order sent.)

## Dogrulanmis adim sirasi (hafta ici, seans sonrasi)

Hepsi `python -m bist_signal_bot ...` ile (Windows: `.venv\Scripts\python.exe -m bist_signal_bot ...`).

1. `daily archive-update --all-active` (~18:45) - gunluk barlari yerel arsive ceker.
2. `forward run-daily --receipt` (~18:50) - tazelik kapisi, karar, cikis/giris, NAV, Turkce paper makbuzu + niyet defteri.
3. `forward health` (~19:10) - kill switch, zincir, veri tazeligi, disk, uyarilar (`--dry-run` / `--notify`).
4. `forward integrity` - hash zincirleri (decisions/outcomes/intents), dondurulmus `portfolios.json` hash'i,
   `trials.sqlite` (`PRAGMA integrity_check`, satir sayisi son kontrol noktasindan (`data/forward/integrity_checkpoint.json`)
   asagi inemez, rowid bosluklari artamaz). Cikis kodu 0 = PASS, 1 = FAIL. Okunamayan her sey FAIL sayilir (fail-closed).
5. `forward backup` - `data/forward` + ledger'in tutarli (sqlite backup API) kopyasi + sirsiz konfigler, sha256 manifestli zip.
   Dogrulama: `forward restore <zip> --verify`; geri yukleme: `forward restore <zip> --to <BOS_DIZIN>` (canli veriyi ezmez).

Zamanlama komutlari (metin): `docs/runbooks/scheduler_windows.md`. Haftalik: `model-loop daily-train --only-if-due`.
Periyodik tatbikat: `security kill-switch-drill` (izole gecici dizinde; gercek kill switch'e dokunmaz).

## Bilinen Yahoo davranisi: ayni gun kapanisi NaN olabilir

Yahoo, seans biter bitmez bugunun gunluk kapanisini bazen gec yayinlar; bar `NaN` ya da hic yok gelebilir. Bu durumda
tazelik kapisi `STALE` doner ve KARAR URETILMEZ. Bu DOGRU (fail-closed) davranistir; veriyi uydurmayin, kapiyi
gevsetmeyin. Cozum: birkac saat sonra ya da ertesi sabah (08:30 civari) `daily archive-update --all-active` ve
`forward run-daily --receipt` komutlarini tekrarlayin (idempotent). Ertesi gun hala eksikse o gun kayitta bos kalir;
geriye donuk doldurmayin.

## Uyari -> yapilacak

| Uyari / durum | Anlami | Yapilacak |
|---|---|---|
| `status=STALE` / `STALE_DATA` | Son bar beklenen seanstan geride veya kapsama dusuk | Yukaridaki Yahoo notu: sonra tekrar dene. Surerse `runbooks/data_stale.md` |
| `status=KILL_SWITCH` / `KILL_SWITCH_TOGGLED` | Kill switch aktif; yeni giris yok, cikislar serbest | `runbooks/kill_switch_active.md`; nedeni anla, bilincli kapat (`security kill-switch deactivate --confirm`) |
| `status=FAILED` | Calisma hatasi (kilit, zincir, fetch...) | `runs.jsonl` son kayit + `errors`; "hash chain broken" ise `forward integrity` |
| `forward integrity` FAIL: `chain_*_broken` | Zincir degistirilmis/eksik/yarim satir | DURUN, dosyayi duzenlemeyin; son dogrulanmis yedegi `restore --verify` ile kontrol edip BOS dizine acin, farki inceleyin; yeni run-daily yapmayin |
| FAIL: `portfolios_v*_hash_mismatch` | Dondurulmus portfoy dosyasi degismis | Dosyayi yedekten karsilastirin; yeniden secim/yeniden dondurma YAPMAYIN (yeni plan gerekir) |
| FAIL: `ledger_integrity_check_failed` / `ledger_unreadable` / `ledger_missing` | trials.sqlite bozuk/yok | Yeni arastirma calistirmayin; son iyi yedekten `trials.sqlite`'i BOS dizine acip karsilastirin |
| FAIL: `ledger_rows_decreased` / `ledger_max_rowid_decreased` / `ledger_rowid_gaps_increased` | Append-only ihlali (satir silinmis) | Ayni: yedekle karsilastirin; kontrol noktasini elle silip PASS'e zorlamayin |
| `forward backup` hata / `restore --verify` FAIL | Zip bozuk veya manifest uyusmuyor | Hemen yeni yedek alin; eski zip'e guvenmeyin |
| Telegram gonderilemedi | Bildirim kanali | `runbooks/telegram_failure.md` (islem etkilenmez) |
| Drawdown / divergence uyarilari | Plan esikleri | `runbooks/forward_paper_plan.md`; parametre degistirmeyin (never retune) |

Her durumda: gercek emir yoktur; sistem yalnizca paper/simulasyondur.
