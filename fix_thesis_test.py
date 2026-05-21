import re

filepath = "bist_signal_bot/review/thesis.py"
with open(filepath, "r") as f:
    content = f.read()

# Fix the scoring logic in score_thesis_strength
new_logic = """
        if not thesis.main_thesis:
            return ThesisStrength.WEAK
        if thesis.counter_thesis and len(thesis.counter_thesis) > len(thesis.main_thesis):
            return ThesisStrength.CONFLICTED
        if thesis.key_risks and len(thesis.key_risks) >= 3:
            return ThesisStrength.MODERATE
        return ThesisStrength.STRONG
"""
content = re.sub(r'        if not thesis\.main_thesis:.*?return ThesisStrength\.STRONG\n', new_logic, content, flags=re.DOTALL)

with open(filepath, "w") as f:
    f.write(content)
