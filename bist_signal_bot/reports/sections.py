from typing import Any
from bist_signal_bot.reports.models import ReportDataBundle, ReportConfig, ReportSection, ReportSectionType

class ReportSectionBuilder:
    def build_sections(self, bundle: ReportDataBundle, config: ReportConfig) -> list[ReportSection]:
        sections = []
        sections.append(self.build_disclaimer_section(config))
        sections.append(self.build_executive_summary(bundle, config))
        sections.append(self.build_scanner_highlights_section(bundle, config))
        sections.append(self.build_paper_summary_section(bundle, config))
        return sections

    def build_disclaimer_section(self, config: ReportConfig) -> ReportSection:
        return ReportSection(
            section_id="disclaimer",
            section_type=ReportSectionType.DISCLAIMER,
            title="Disclaimer",
            body_markdown="This report is for research purposes only. Not investment advice. No real orders are sent."
        )

    def build_executive_summary(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(
            section_id="executive_summary",
            section_type=ReportSectionType.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            body_markdown=f"Research summary for {config.report_type.value}.",
            summary=bundle.source_summaries
        )

    def build_market_regime_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="market_regime", section_type=ReportSectionType.MARKET_REGIME, title="Market Regime", body_markdown="Regime analysis.")

    def build_scanner_highlights_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="scanner_highlights", section_type=ReportSectionType.SCANNER_HIGHLIGHTS, title="Scanner Highlights", body_markdown="Recent scanner candidates.")

    def build_risk_summary_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="risk_summary", section_type=ReportSectionType.RISK_SUMMARY, title="Risk Summary", body_markdown="Risk metrics.")

    def build_ml_summary_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="ml_summary", section_type=ReportSectionType.ML_SUMMARY, title="ML Summary", body_markdown="ML prediction analysis.")

    def build_adaptive_summary_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="adaptive_summary", section_type=ReportSectionType.ADAPTIVE_SUMMARY, title="Adaptive Summary", body_markdown="Adaptive updates.")

    def build_paper_summary_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="paper_summary", section_type=ReportSectionType.PAPER_SUMMARY, title="Paper Trading Summary", body_markdown="Simulated execution details. No real orders sent.")

    def build_research_ledger_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="research_ledger", section_type=ReportSectionType.RESEARCH_LEDGER, title="Research Ledger", body_markdown="Ledger entries.")

    def build_signal_journal_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="signal_journal", section_type=ReportSectionType.SIGNAL_JOURNAL, title="Signal Journal", body_markdown="Journal entries.")

    def build_attribution_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="attribution", section_type=ReportSectionType.ATTRIBUTION, title="Attribution", body_markdown="Attribution reports.")

    def build_operations_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="operations", section_type=ReportSectionType.RUNTIME_OPERATIONS, title="Operations", body_markdown="System monitoring and operations.")

    def build_appendix_section(self, bundle: ReportDataBundle, config: ReportConfig) -> ReportSection:
        return ReportSection(section_id="appendix", section_type=ReportSectionType.APPENDIX, title="Appendix", body_markdown="Extra data.")
