def check_readiness(include_data_catalog=False):
    res = {"ready": True}
    if include_data_catalog:
        res["data_catalog_ready"] = True
    return res
