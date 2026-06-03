Phase 106 - Local Model Explainability, Feature Attribution, Decision Trace, Model Interpretability, Counterfactual Research ve Explanation Governance Katmanı başarıyla uygulandı.

1. Eklenen/güncellenen dosyalar:
- bist_signal_bot/explainability altına: feature_attribution.py, permutation.py, sensitivity.py, decision_trace.py, rule_trace.py, counterfactuals.py, cohorts.py, model_introspection.py, governance.py, reporting.py, storage.py eklendi.
- bist_signal_bot/app/explainability_app.py
- settings.py ve .env.example
- CLI entegrasyonu (commands.py)
- Model, Strategy ve Scanner modellerine entegrasyon
- Docs hub ve örnek workflows eklendi.

2. Mimari tamamen local-first olarak kuruldu.
3. Modeller oluşturuldu ve Enum'lar eklendi (ExplanationStatus, vs.)
4-10. Bütün behavior/engine sınıfları (Feature Attribution, Permutation, Sensitivity, Counterfactual vb.) implement edildi.
11-15. Entegrasyonlar sağlandı. Report ve App factory fonksiyonları eklendi.
16. CLI komutları yazıldı: python -m bist_signal_bot explainability <command>
17. Audit ve Notification entegrasyonu yapıldı.
18. README ve docs güncellendi.
19. 27 test yazıldı ve başarıyla pass etti.
20. Hedeflenen çalıştırma komutları test edilerek CLI üzerinden sunuldu.
21. Phase 107'ye hazırdır.
