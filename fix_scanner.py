import re

filepath = "bist_signal_bot/scanner/engine.py"
with open(filepath, "r") as f:
    content = f.read()

if "add_to_review" not in content:
    add_param = """    add_to_review: bool = False
    review_priority: Optional[str] = None"""

    # insert into ScanRequest
    content = re.sub(r'(class ScanRequest\(BaseModel\):.*?)(?=\nclass |\Z)', r'\1\n' + add_param + '\n', content, flags=re.DOTALL)

    # Also we should import review item inside process
    process_review = """
        if getattr(request, 'add_to_review', False):
            try:
                from bist_signal_bot.app.review_app import create_review_inbox_manager
                manager = create_review_inbox_manager(settings=self.settings)
                # mock adding
                item = manager.add_manual_item("SCAN_RESULT", "Scanner added", "Auto added from scanner")
                if "metadata" not in summary:
                    summary["metadata"] = {}
                summary["metadata"]["review_item_id"] = item.item_id
            except Exception as e:
                pass
"""
    # Insert somewhere in process_batch
    content = re.sub(r'(summary\["total_signals"\] = total_signals)', r'\1' + process_review, content)

    with open(filepath, "w") as f:
        f.write(content)
