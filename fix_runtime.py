import re

filepath = "bist_signal_bot/runtime/orchestrator.py"
with open(filepath, "r") as f:
    content = f.read()

if "add_signals_to_review" not in content:
    add_param = """    add_signals_to_review: bool = False
    review_auto_checklist: bool = True"""

    # insert into RuntimePipelineConfig
    content = re.sub(r'(class RuntimePipelineConfig\(BaseModel\):.*?)(?=\nclass |\Z)', r'\1\n' + add_param + '\n', content, flags=re.DOTALL)

    with open(filepath, "w") as f:
        f.write(content)
