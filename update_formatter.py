import re

with open("bist_signal_bot/notifications/formatter.py", "r") as f:
    content = f.read()

new_formatter = """

    def format_pattern_feature_summary(self, result: Any, symbol: str | None = None, level: str | None = None) -> str:
        lines = [
            "<b>BIST Bot Pattern Feature Özeti</b>",
            "",
            f"Sembol: {self._escape(symbol or 'Bilinmiyor')}",
            f"Seviye: {self._escape(level or 'Bilinmiyor')}",
            f"İstenen: {result.requested_count}",
            f"Başarılı: {result.success_count}",
            f"Başarısız: {result.failed_count}",
        ]

        if result.success_count > 0:
            lines.append(f"Üretilen kolon: {len(result.output_data.columns)}")

        return "\\n".join(lines)
"""

content += new_formatter

with open("bist_signal_bot/notifications/formatter.py", "w") as f:
    f.write(content)
