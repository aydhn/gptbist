# Disclosure Intelligence

## Mimari
Disclosure Intelligence modülü BIST hisseleri için finansal açıklamalar, KAP duyuruları, haber özetleri ve şirket raporları gibi metinlerin yerel bir veritabanında (offline JSONL) işlenerek risk ve anlatı (narrative) değerlendirmesi yapılması amacıyla tasarlanmıştır. Tüm süreç (import, classification, text extraction) tamamen yerel olarak, deterministik algoritmalarla çalışır; hiçbir aşamada Cloud LLM, web scraping veya OpenAI API çağrısı yapılmaz.

## Veri Altyapısı ve Format
Sistem, `data/disclosures/records/disclosure_records.jsonl` üzerinde append-only (sadece ekleme yapılabilir) olarak çalışır. Dosyalar CSV, JSON ve TXT klasörleri aracılığıyla içeri aktarılabilir (import).

Örnek CSV Formatı:
```csv
external_id,title,body,disclosure_type,published_at,symbols
ext-101,"Aselsan Yeni İhale Aldı","ASELS 10 milyon dolar değerinde...","CONTRACT_TENDER","2024-05-10T12:00:00Z","ASELS"
```

## Anahtar Bileşenler
1. **Importer (`importer.py`)**: CSV, JSON ve düz metin klasörlerinden verileri içeri aktarır, ID oluşturur. Dry-run moduna ve zorunlu `--confirm` katmanına sahiptir.
2. **Normalizer (`normalizer.py`)**: Text içindeki gizli kalması gereken bilgileri redact eder (API key, IBAN vb.). Satır aralıklarını düzeltir.
3. **Classifier (`classifier.py`)**: Metindeki anahtar kelimelere göre duyuru tipini, duygu durumunu (sentiment) ve ciddiyet derecesini (severity) belirler.
4. **Entity Linker (`entity_linker.py`)**: Metindeki sembolleri, şirket isimlerini tespit edip birbirleriyle bağlar.
5. **Risk Tagger (`risk_tags.py`)**: Olası iflas, dava, sulandırma veya kâr baskısı gibi riskli terimleri tespit edip risk skoru atar.
6. **Event Extractor (`event_extractor.py`)**: Duyuru metinleri içindeki tarihleri çözümleyerek Takvim Olayları (Event Calendar) oluşturma kapasitesine sahiptir.
7. **Impact Assessor (`impact.py`)**: Toplanan risk tag'lerine ve severity seviyelerine bakarak bir hikaye risk skoru (Narrative Risk Score) hesaplar.
8. **Digest Builder (`digest.py`)**: Özet (digest) raporları üreterek aşırı bilgi yükünü tekilleştirir ve Review Inbox üzerinden iletilmek üzere sunar.

## Kurallar ve Kısıtlamalar
1. Gerçek emir gönderimi **yoktur**. Bu analiz yalnızca bilgi amaçlıdır.
2. Fiyat yönü ("Hisse yarın tavan olacak") yönlendirmesi veya tahmin yapılması **kesinlikle yasaktır**.
3. Çıktılar Evidence Card ve Review Inbox tarafından kullanılır, otomatik sinyal tetiklemez.

## CLI Kullanımı
```bash
python -m bist_signal_bot disclosures import --file my_data.csv --dry-run
python -m bist_signal_bot disclosures classify DISCLOSURE_ID
python -m bist_signal_bot disclosures assess DISCLOSURE_ID
```
