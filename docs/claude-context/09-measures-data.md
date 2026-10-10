# 09 - BIST tedbir (VBTS) verisi

**Kaynak:** KAP'taki "Borsa Istanbul A.S." duyurulari (`POST https://www.kap.org.tr/tr/api/disclosure/members/byCriteria`,
oid `4028e4a14bcf2a06014be4d7e6e256b6`, 6 aylik pencereler). Filtre: ozette "Volatilite" gecenler (hisse bazli VBTS).
Govde: borsapy `KAPProvider().get_disclosure_content(id)` -> HTML -> `measures/parser.py`.

**Kapsam:** duyuru tarihcesi ~2018-02+ (en eski kayit `measures status` ile gorulur). Tur: `GROSS_SETTLEMENT` (brut takas),
`SINGLE_PRICE` (tek fiyat), `ORDER_PACKAGE` (emir paketi). Tablo: `data/measures/measures.csv`
(symbol,type,start,end,announcement_id,publish_date,source,fetched_at); ham govdeler `data/measures/raw/`.

**Komutlar:** `measures sync [--since YYYY-MM-DD] [--max-bodies N]` (>=2.5 sn/istek, yeniden baslatilabilir),
`measures status`, `measures check SYMBOL YYYY-MM-DD`.
Kurulum (ayri ortamda, repo .venv'e DEGIL): `pip install pykap==0.2.0 borsapy==0.11.0` (surumler sabit; yalniz borsapy govde icin gerekli).

**Gunluk kural:** `DAILY_MEASURE_RULE_ENABLED` (varsayilan kapali; `config/defaults.py`'ye eklenmesi gerekir: `False`).
Acikken ve tablo varken: tedbirli (3 tur) hissede GIRIS dolmaz (`Fills.measure_blocked`, neden 'measure'), CIKIS ilk tedbirsiz
seansa ertelenir (kilitli limit cikisi ile ayni desen). Tablo yoksa kural uygulanmaz (`measure_report(ctx)["reason"]=="no_table"`);
duyuru tarihcesi disindaki seanslar `share_dates_covered` ile raporlanir.

**Bilinen eksikler:**
- Erken sonlandirma / uzatma duyurulari modellenmedi (bitis tarihi ilk duyurudaki tarihtir).
- Acigga satis / kredili islem yasaklari (ayri tedbirler) yok.
- Yatirimci bazli tedbirler haric; ozeti "Volatilite" icermeyen duyurular atlanir. Cumle kalibi disi govdeler uyariyla atlanir.
- Belgesiz (undocumented) KAP ucu: haber verilmeden degisebilir/engellenebilir.
- Lisans: borsapy README'sine gore yalnizca kisisel/egitim kullanimi; KAP verisinin yeniden dagitimi yapilmamali.
