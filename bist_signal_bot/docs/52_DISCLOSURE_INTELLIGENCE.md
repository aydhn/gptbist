# Disclosure Intelligence

## Mimari
BIST Signal Bot Disclosure Intelligence katmanı, şirketlerin açıklamalarını (KAP, haber vs.) tamamen offline ortamda import edip risk skoru üreten ve narrative analysis yapan bir araştırma modülüdür.

## CSV/JSON/TXT Import Formatı
CSV import'lar `external_id, title, body, disclosure_type, published_at, symbols` kolonlarını destekler. JSON list of objects olarak alınır. TXT dosyası doğrudan text body olarak değerlendirilir.

## Web Scraping Yoktur
HTML parsing veya web scraping işlemi yapılmaz. Sistem OpenAI veya herhangi bir Cloud LLM servisini kullanmaz. Metin analizi tamamen deterministic veya rule-based yapıdadır.

## Yasal Uyarı
Disclosure metadata fiyat yönü tahmini yapmaz. Yatırım tavsiyesi değildir. Gerçek piyasada işlem gerçekleştirmez.
