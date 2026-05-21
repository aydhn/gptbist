import re

filepath = "bist_signal_bot/app/healthcheck.py"
with open(filepath, "r") as f:
    content = f.read()

if "review_status" not in content:
    review_check = """
        # Review status
        try:
            from bist_signal_bot.app.review_app import create_review_inbox_manager
            manager = create_review_inbox_manager(settings=self.settings)
            summary = manager.summary()
            status["review_status"] = "OK"
            status["review_items_total"] = summary.total_items
            status["review_items_new"] = summary.new_count
        except Exception as e:
            status["review_status"] = f"ERROR: {str(e)}"
"""
    # Insert before the end of the run method
    content = re.sub(r'(return status\s*\Z)', review_check + r'\n        \1', content)

    with open(filepath, "w") as f:
        f.write(content)
