# Portfolio Construction

## 1. Amacı ve Özellikleri
Portfolio Construction Katmanı (Phase 76), tekil strateji sinyallerini alır ve korelasyon, sektör konsantrasyonu, risk bütçesi, execution cost ve likidite durumunu göz önüne alarak dengeli bir araştırma sepeti oluşturur.

Bu katman gerçek bir emir sistemi **değildir**. Broker API çağırmaz ve sadece research (araştırma) amaçlıdır.

## 2. Aday Kaynakları (Candidates)
- Scanner ve signal modülünden gelen güncel sinyaller.
- Calibration ve Strategy Scorecard metrikleriyle puanlandırılmış olan adaylar.
- Liquidity ve execution simülasyonlarıyla filtrelenen enstrümanlar.

## 3. Weighting Methods
- `EQUAL_WEIGHT`: Tüm adaylara eşit ağırlık verilir.
- `CONFIDENCE_WEIGHTED`: Sinyalin calibrated veya raw confidence değerine göre ağırlıklandırılır.
- `SCORE_WEIGHTED`: Execution, monte carlo, validation metrikleri toplanarak oluşturulan final_score üzerinden ağırlıklandırılır.
- `RISK_PARITY_LITE`: Volatiliteye ters orantılı (inverse volatility) risk dağıtımı yapılır.

## 4. Constraint (Kısıt) Motoru
Modelin dengeli bir portföy ürettiğinden emin olmak için tanımlanmış sınırlar:
- Max Symbol Weight (örn: 0.20)
- Max Sector Weight (örn: 0.35)
- Max Correlation Cluster Weight (örn: 0.45)
- Max Turnover ve Cost Drag

## 5. Rebalance Simulation ve Risk Budget
Yeni bir sinyal bütünü oluşturulduğunda, `RebalanceSimulator` mevcut ağırlıklarla (current weights) hedeflenenleri kıyaslayarak (ADD, REMOVE, INCREASE, vb.) aksiyonlar üretir. Bu aksiyonlar tamamen varsayımsaldır. Aynı zamanda, risk katkı oranları (Contribution to Risk) hesaplanarak riskin tek bir hissede toplanması önlenir.

## 6. Güvenlik ve Uyumluluk
- Çıktılarda otomatik olarak *Research Only* ve *Not Investment Advice* disclaimer'ı yer alır.
- Governance kısıtlamalarına göre, raporlarda "execute", "buy order" gibi kesin talimat dilleri engellenmiştir.
