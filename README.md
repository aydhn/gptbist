# BIST Signal Bot

## 1. Proje Özeti
BIST Signal Bot is a Python-based algorithmic signal generator for Borsa Istanbul designed for local execution without a UI or dashboard.

## 2. Güvenlik Sınırları
- Dashboard yok.
- Web panel yok.
- HTML scraping yok.
- Ücretli servis yok.
- OpenAI API yok.
- Cloud LLM yok.
- Broker API yok.
- Gerçek emir gönderimi yok.

## 3. Research-only no-real-order yaklaşımı
This tool generates signals for research and offline backtesting only. No real orders are sent to any market.

## 4. Hızlı Kurulum
```bash
pip install -r requirements.txt
python -m bist_signal_bot bootstrap init
```

## 5. Offline Demo
```bash
python -m bist_signal_bot bootstrap demo --json
```

## 6. Ana Modüller
See docs/77_FINAL_MVP_HANDOFF.md for the list of major modules.

## 7. CLI Komut Haritası
See docs/80_FINAL_COMMAND_MAP.md for all available commands.

## 8. Günlük Operator Rutini
```bash
python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog
python -m bist_signal_bot ops status
python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog
```

## 9. Geliştirici Başlangıç Noktası
See docs/30_DEVELOPER_GUIDE.md and examples/developer_next_feature_flow.md

## 10. QA / Ops / Final Audit
Run `python -m bist_signal_bot qa release-gate`, `python -m bist_signal_bot ops status`, and `python -m bist_signal_bot final-audit run`.

## 11. Final Handoff
```bash
python -m bist_signal_bot final-handoff build
python -m bist_signal_bot final-handoff release-pack
```

## 12. Known Limitations
- No real-time market data streaming.
- No live broker execution.

## 13. Roadmap
See docs/79_POST_RELEASE_ROADMAP.md for details on phases 101+.

## 14. Sık Kullanılan Komutlar
```bash
python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run
```

## Final Local Kontrol Sırası
```bash
python -m bist_signal_bot bootstrap validate --profile STANDARD
python -m bist_signal_bot bootstrap demo --json
python -m bist_signal_bot healthcheck --bootstrap --ops --cli-ux --docs-hub --data-catalog --feature-store --model-registry --monitoring --leaderboard --orchestrator --final-audit --final-handoff
python -m bist_signal_bot qa release-gate --include-bootstrap --include-ops --include-cli-ux --include-docs-hub --include-data-catalog --include-feature-store --include-model-registry --include-monitoring --include-leaderboard --include-orchestrator --include-final-audit --include-final-handoff
python -m bist_signal_bot ops readiness --include-bootstrap --include-data-catalog --include-feature-store --include-model-registry --include-monitoring --include-leaderboard --include-orchestrator --include-final-audit --include-final-handoff
python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --symbols ASELS THYAO --dry-run --json
python -m bist_signal_bot final-audit go-no-go --json
python -m bist_signal_bot final-handoff build --save --json
python -m bist_signal_bot final-handoff report --latest
pytest
```
