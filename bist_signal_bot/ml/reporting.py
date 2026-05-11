import pandas as pd
from typing import Any
from bist_signal_bot.ml.models import MLDatasetResult

def ml_dataset_result_to_dict(result: MLDatasetResult, include_preview: bool = False) -> dict[str, Any]:
    d = result.summary()
    d["schema"] = result.schema_.summary()

    if include_preview and result.data is not None and not result.data.empty:
        # just a tiny preview of the head
        preview_cols = result.schema_.metadata_cols[:2] + result.schema_.label_cols[:2]
        available_cols = [c for c in preview_cols if c in result.data.columns]
        d["preview"] = result.data[available_cols].head(3).to_dict(orient="records")
    return d

def dataset_summary_dataframe(result: MLDatasetResult) -> pd.DataFrame:
    # A single row dataframe summarizing the run
    summary = ml_dataset_result_to_dict(result)
    # flatten simple dicts if needed
    flat_summary = {
        "status": summary["status"],
        "symbols": summary["symbols"],
        "row_count": summary["row_count"],
        "feature_count": summary["feature_count"],
        "label_count": summary["label_count"],
        "train_rows": summary["train_rows"],
        "test_rows": summary["test_rows"],
        "elapsed_seconds": summary["elapsed_seconds"],
    }
    return pd.DataFrame([flat_summary])

def format_ml_dataset_text(result: MLDatasetResult) -> str:
    lines = []
    lines.append("BIST Bot ML Dataset Result Summary")
    lines.append("=" * 40)
    lines.append(f"Status: {result.status.value}")
    lines.append(f"Symbols: {len(result.request.symbols)}")
    lines.append(f"Rows: {result.row_count}")
    lines.append(f"Features: {result.feature_count}")
    lines.append(f"Labels: {result.label_count}")
    lines.append(f"Task Type: {result.request.task_type.value}")

    if result.train_data is not None and result.test_data is not None:
        lines.append(f"Train/Test Rows: {len(result.train_data)} / {len(result.test_data)}")

    if result.schema_.label_cols and result.data is not None and not result.data.empty:
        # Check label distribution for the first label
        lbl_col = result.schema_.label_cols[0]
        if lbl_col in result.data.columns:
            counts = result.data[lbl_col].value_counts(dropna=False).to_dict()
            dist = ", ".join([f"{k}: {v}" for k, v in counts.items()])
            lines.append(f"Label Distribution ({lbl_col}): {dist}")

    lines.append("-" * 40)
    if result.output_files:
        lines.append("Output Files:")
        for k, v in result.output_files.items():
            lines.append(f"  - {k}: {v}")
    else:
        lines.append("No files saved.")

    if result.issues:
        lines.append("-" * 40)
        lines.append("Issues:")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    lines.append("=" * 40)
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_ml_dataset_markdown(result: MLDatasetResult) -> str:
    lines = []
    lines.append("## BIST Bot ML Dataset Result Summary")
    lines.append("")
    lines.append(f"- **Status:** {result.status.value}")
    lines.append(f"- **Symbols:** {len(result.request.symbols)}")
    lines.append(f"- **Rows:** {result.row_count}")
    lines.append(f"- **Features:** {result.feature_count}")
    lines.append(f"- **Labels:** {result.label_count}")
    lines.append(f"- **Task Type:** {result.request.task_type.value}")

    if result.train_data is not None and result.test_data is not None:
        lines.append(f"- **Train/Test Rows:** {len(result.train_data)} / {len(result.test_data)}")

    if result.schema_.label_cols and result.data is not None and not result.data.empty:
        lbl_col = result.schema_.label_cols[0]
        if lbl_col in result.data.columns:
            counts = result.data[lbl_col].value_counts(dropna=False).to_dict()
            dist = ", ".join([f"{k}: {v}" for k, v in counts.items()])
            lines.append(f"- **Label Distribution ({lbl_col}):** {dist}")

    if result.output_files:
        lines.append("")
        lines.append("### Output Files:")
        for k, v in result.output_files.items():
            lines.append(f"- `{k}`: {v}")

    if result.issues:
        lines.append("")
        lines.append("### Issues:")
        for issue in result.issues:
            lines.append(f"- {issue}")

    lines.append("")
    lines.append(f"> _{result.disclaimer}_")
    return "\n".join(lines)
