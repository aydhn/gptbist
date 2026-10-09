# Çok günlü ufuk — kaynaklı araştırma notu (2026-10-10)

Web araması özetleri (özet/özet-kayıt düzeyi; tam metinler doğrulanmadı). Kazanç vaadi değildir; hipotez kaynağıdır.
Tüm hipotezler yine aynı `CandidateGate`'ten geçer ve trial ledger'a yazılır.

## BIST anomalileri
- BIST'te kesitsel momentum / kısa vadeli ters dönüşün maliyet sonrası doğrudan testi bulunamadı.
  BIST'te zaman serisi ters dönüş piyasa durumuna (state) bağlı: Demirer, Yüksel & Yüksel (2017), RIBAF —
  [IDEAS](https://ideas.repec.org/a/eee/riibaf/v42y2017icp1445-1454.html).
- Maliyet: kısa vadeli ters dönüş maliyete en duyarlı; kârın büyük kısmı küçük hisselerin aşırı işleminden gelir
  ([NBER, Frazzini-Israel-Moskowitz](https://conference.nber.org/conf_papers/f68262/f68262.pdf)). Kesitsel momentum için
  gerçekçi maliyetlere dayanıklı bulgular var, en iyi tutuş ~6 ay
  ([Imperial](https://spiral.imperial.ac.uk/entities/publication/af9f6a4b-796a-4f37-bd4d-c214b433ab21)).
  Sınır pazarlarda kısa vadeli momentum daha güçlü
  ([UCT](https://open.uct.ac.za/items/2e9c4d25-aae8-4bd9-93f8-5b6285c9edef)).
- Ay dönümü (turn-of-the-month): 24 BIST sektör endeksinden 14'ünde bulgu, örneklem/yönteme duyarlı
  ([KTÜ](https://avesis.ktu.edu.tr/yayin/0b8c2334-fd4e-45b9-a8e9-a14ee1b07e89/testing-of-intra-month-turn-of-the-month-and-turn-of-the-year-effect-effects-in-bist-sector-and-sub-sector-indexes)).
- Düşük beta/oynaklık: belirli beta aralığında anomali var, çok düşük/çok yüksek betada getiri düşer
  ([Özyeğin](https://eresearch.ozyegin.edu.tr/handle/10679/7606), [GTÜ](https://acikerisim.gtu.edu.tr/items/08469c3d-ac8e-479c-92f3-1a50cf6e6eb1)).
- Hacim şoku için BIST çalışması bulunamadı (yalnız genel literatür).

## Makro / faiz (nakit faizi benchmark'ı için)
- TCMB politika faizi %37 (10 Eylül 2026'da sabit); sonraki PPK 22 Ekim 2026; yıl sonu medyan beklenti ~%35
  ([GCM](https://www.gcmyatirim.com.tr/egitim/makaleler/tcmb-2026-faiz-karari-takvimi-toplanti-tarihleri-ve-faiz-oranlari),
  [Politikam](https://www.politikam.com/merkez-bankasi-ekim-ayi-faiz-karari-ne-zaman-aciklanacak-tcmb-2026-ppk-toplanti-tarihi-ve-detaylari)).
- TL mevduat stopajı: ≤6 ay %17,5, ≤1 yıl %15, >1 yıl %10; 31.12.2026'ya uzatıldı (kaynaklar kısmen çelişkili; Resmî Gazete
  20.06.2026 / 33286 / CK 11444'ten doğrulanmalı) — [Yöntem YMM](https://www.yontemymm.com.tr/mali-aciklamalar/2026-041-tl-mevduat-hesaplarinda-uygulanan-stopaj-oranlarinin-suresi-uzatildi).
- Kodda `PAPER_CASH_INTEREST_ANNUAL=0.30` / `_WITHHOLDING=0.15` yer tutucudur. Gerçek mevduat/repo faizi kullanıcıdan istenir.
  Benchmark olarak politika faizi (%37) ve stopaj sonrası net getiri ayrı raporlanır.
