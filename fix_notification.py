import re

filepath = "bist_signal_bot/notifications/formatter.py"
with open(filepath, "r") as f:
    content = f.read()

if "def format_review_inbox_summary" not in content:
    review_formatter = """

def format_review_item(item) -> str:
    return f"[{item.symbol}] Review Item: {item.status.value}\\n{item.summary}\\n{item.disclaimer}"

def format_review_decision(decision) -> str:
    return f"Decision: {decision.decision_type.value}\\nReason: {decision.reason}\\n{decision.disclaimer}"

def format_review_inbox_summary(summary) -> str:
    lines = [
        "BIST Bot Analyst Review Özeti",
        "",
        f"New: {summary.new_count}",
        f"In Review: {summary.in_review_count}",
        f"Watch Only: {summary.watch_only_count}",
        f"Approved Research: {summary.approved_research_count}",
        f"Due Follow-ups: {summary.waiting_followup_count}",
        "",
        "Bu çıktı analist araştırma review özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\\n".join(lines)

def format_review_followups(items) -> str:
    if not items:
        return "No due follow-ups."
    lines = ["Due follow-ups:"]
    for i in items:
        lines.append(f"- {i.symbol}")
    return "\\n".join(lines)
"""
    with open(filepath, "a") as f:
        f.write(review_formatter)
