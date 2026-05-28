with open("bist_signal_bot/factors/storage.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "f.write(json.dumps(data, default=str)" in line:
        lines[i] = '            f.write(json.dumps(data, default=str) + "\\n")\n'

with open("bist_signal_bot/factors/storage.py", "w") as f:
    f.writelines(lines)

with open("bist_signal_bot/factors/reporting.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "format_factor_scores_text" in line or "format_factor_exposure_text" in line or "format_sector_rotation_text" in line or "format_theme_exposure_text" in line or "format_factor_report_markdown" in line:
        pass # just to check
