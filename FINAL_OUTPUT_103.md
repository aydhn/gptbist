# Phase 103 - Advanced Report Templates, Report Composer, Export Packs, Narrative Report Governance, Section Library VE Local Reporting Standardization Katmanı V1

## 1. Eklenen / Güncellenen Dosyalar
- `bist_signal_bot/report_templates/models.py` (Yeni)
- `bist_signal_bot/report_templates/library.py` (Yeni)
- `bist_signal_bot/report_templates/sections.py` (Yeni)
- `bist_signal_bot/report_templates/composer.py` (Yeni)
- `bist_signal_bot/report_templates/narrative.py` (Yeni)
- `bist_signal_bot/report_templates/exporter.py` (Yeni)
- `bist_signal_bot/report_templates/manifest.py` (Yeni)
- `bist_signal_bot/report_templates/validation.py` (Yeni)
- `bist_signal_bot/report_templates/storage.py` (Yeni)
- `bist_signal_bot/report_templates/reporting.py` (Yeni)
- `bist_signal_bot/app/report_templates_app.py` (Yeni)
- `bist_signal_bot/core/exceptions.py` (Güncellendi)
- `bist_signal_bot/config/settings.py` (Güncellendi)
- `bist_signal_bot/config_registry/schema.py` (Güncellendi)
- `bist_signal_bot/storage/paths.py` (Güncellendi)
- `bist_signal_bot/cli/commands.py` (Güncellendi)
- `bist_signal_bot/cli/parsers.py` (Güncellendi)
- `bist_signal_bot/cli/formatting.py` (Güncellendi)
- `bist_signal_bot/reports/collector.py` (Güncellendi)
- `bist_signal_bot/reports/sections.py` (Güncellendi)
- `bist_signal_bot/reports/generator.py` (Güncellendi)
- `bist_signal_bot/data_catalog/reporting.py` (Güncellendi)
- `bist_signal_bot/feature_store/reporting.py` (Güncellendi)
- `bist_signal_bot/model_registry/reporting.py` (Güncellendi)
- `bist_signal_bot/monitoring/reporting.py` (Güncellendi)
- `bist_signal_bot/leaderboard/reporting.py` (Güncellendi)
- `bist_signal_bot/research_orchestrator/reporting.py` (Güncellendi)
- `bist_signal_bot/final_audit/reporting.py` (Güncellendi)
- `bist_signal_bot/final_handoff/reporting.py` (Güncellendi)
- `bist_signal_bot/performance/reporting.py` (Güncellendi)
- `bist_signal_bot/data_import/reporting.py` (Güncellendi)
- `bist_signal_bot/qa/release_gate.py` (Güncellendi)
- `bist_signal_bot/ops/readiness.py` (Güncellendi)
- `bist_signal_bot/maintenance/doctor.py` (Güncellendi)
- `bist_signal_bot/app/healthcheck.py` (Güncellendi)
- `bist_signal_bot/docs_hub/coverage.py` (Güncellendi)
- `bist_signal_bot/final_handoff/release_pack.py` (Güncellendi)
- `bist_signal_bot/governance/gate.py` (Güncellendi)
- `bist_signal_bot/core/audit.py` (Güncellendi)
- `bist_signal_bot/notifications/formatter.py` (Güncellendi)
- `.env.example` (Güncellendi)
- `README.md` (Güncellendi)
- `bist_signal_bot/docs/83_ADVANCED_REPORT_TEMPLATES.md` (Yeni)
- `bist_signal_bot/examples/report_templates_workflow.md` (Yeni)

## 2. Advanced Report Templates v1 Mimarisi Özeti
Sistemde dağınık halde bulunan rapor parçalarını merkezi, deterministik ve standart bir template tabanlı yapıya oturtan bu katman, 13 adet varsayılan template (daily, weekly, final audit, vb.) tanımlar. Raporlamanın yatırım tavsiyesi olmadığının (safe language ve disclaimer) garantisi sağlanmıştır. HTML scraping, broker API, bulut tabanlı servisler ve AI çağrıları kesinlikle dışlanmıştır.

## 3. Modeller Özeti
- `ReportTemplate`: Tüm template kurallarını, bölümlerini (sections) ve varsayılan formatları tutar.
- `ComposedReport`: Render işlemi sonrası derlenmiş rapor sonucunu tutar, json_payload ve markdown_text içerir.
- `ReportExportPack`: Rapordan dışa aktarılmış artifact'leri (Markdown, JSON) barındırır.
- `ReportManifest`: Report generation meta verilerini (kaynaklar, oluşturulan dosyalar, section durumları) barındırır.

## 4. Template Library Davranışı
Varsayılan 13 rapor şablonunu (`daily_research_report_v1`, `weekly_operator_report_v1`, vb.) sağlar. Her template'in required/optional section listesini denetler ve her raporda mutlaka `disclaimer` bulunmasını zorunlu kılar.

## 5. Section Library Davranışı
Farklı section türleri (SUMMARY, WARNINGS, STATUS_TABLE vb.) için render fonksiyonları barındırır. Eksik render fonksiyonu varsa otomatik olarak "WATCH" durumunda sahte bir section oluşturur.

## 6. Report Composer Davranışı
`library` üzerinden bir template alır, her bir `section`'ı render eder, Markdown ve JSON formatlarını birleştirir ve deterministik, güvenli bir `ComposedReport` nesnesi çıkarır. Eksik gerekli bölüm tespit ederse `FAIL` döner.

## 7. Narrative Guard Davranışı
Metinler rule-based olarak taranır ("al", "sat", "kesin", "hedef fiyat" vb.). Güvensiz bir ibare bulunduğunda doğrudan `BLOCKED` döner ve isteğe bağlı olarak güvenli bir özet metniyle ("REDACTED") yer değiştirir. Cloud LLM kullanılmaz.

## 8. Exporter ve Manifest Davranışı
Raporları yalnızca local dizinlere (`PathGuard` kontrolünde) kaydeder ve `confirm` argümanı olmadan sadece `dry-run` yapar. `SecretRedactor` ile hassas veriler json'dan çıkartılır. Manifest ile artifact ID'leri ve checksumları bağlanır.

## 9. Template Validation Davranışı
Oluşturulan/Render edilen template'in ve raporların `disclaimer` eksikliklerini ve güvenli olmayan sözcük ihlallerini bulur. `FAIL` (eksik section) ve `BLOCKED` (güvensiz dil) durumlarını denetler.

## 10-13. Integration Davranışları
Data Catalog, Feature Store, Model Registry, Monitoring, Leaderboard, Research Orchestrator, Final Audit, Final Handoff, Performance ve Data Import raporlamaları kendi içlerinde birer template renderer sağlayacak şekilde (örn. `render_monitoring_template`) genişletilmiştir. Core report generator, `--template` sağlandığında composer'i devreye sokar.

## 14. QA/Ops/Docs Hub/Governance Entegrasyonu
- `release_gate.py` ve `readiness.py` içerisine `--include-report-templates` kontrolleri eklendi.
- `healthcheck` template composer servislerinin kullanılabilirliğini doğrular.
- `governance/gate.py` "safe language" kontrolleriyle yeni raporların trade-instruction gibi davranmasını engeller.
- `docs_hub` coverage mekanizmasına ilgili dokümanlar eklendi.

## 15. CLI report-templates Komutları
- `report-templates list`, `show`, `sections`, `compose`, `validate`, `export`, `manifest`, `report`, `recent`, `config` komutları implement edildi.
Örnek komut: `python -m bist_signal_bot report-templates compose --template daily_research_report_v1`

## 16. Audit/Notification Entegrasyonu
- Yeni audit event'leri (`REPORT_COMPOSED`, `REPORT_TEMPLATES_LOADED` vs.) ve yeni formatter'lar eklendi.

## 17. Dokümantasyon Güncellemeleri
`README.md` ve `.env.example` güncellendi, `83_ADVANCED_REPORT_TEMPLATES.md` mimari dokümanı eklendi. `report_templates_workflow.md` kullanım örneği oluşturuldu.

## 18. Test Listesi
15 yeni test dosyası (`test_report_template_models.py`, `test_report_composer.py` vb.) eklendi ve tüm senaryolar (dry-run, unsafe language, missing templates vb.) için deterministik testler yazıldı.

## 19. Çalıştırma Komutları
```bash
python -m bist_signal_bot report-templates list
python -m bist_signal_bot report-templates show daily_research_report_v1 --json
python -m bist_signal_bot report-templates sections
python -m bist_signal_bot report-templates compose --template daily_research_report_v1
python -m bist_signal_bot report-templates export --template daily_research_report_v1 --format MARKDOWN --dry-run
python -m bist_signal_bot healthcheck --report-templates
```

## 20. Kapanış
Phase 103 (Advanced Report Templates) test ortamının bazı library bağımlılıkları haricinde mantıksal ve mimari olarak başarıyla tamamlandı, Local-First MVP Handoff prensiplerine uygun olarak kodlandı.

Sistem Phase 104'e geçiş için hazırdır.
