def run_daily_report(dry_run=False, include_data_catalog=False):
    res = {"report": "daily"}
    if include_data_catalog:
         res["data_catalog_section"] = "included"
    return res
