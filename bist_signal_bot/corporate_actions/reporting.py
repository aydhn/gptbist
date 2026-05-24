
def corporate_action_to_dict(action): return action.model_dump()
def adjustment_factor_to_dict(factor): return factor.model_dump()
def adjusted_price_result_to_dict(result): return result.model_dump()
def data_issue_to_dict(issue): return issue.model_dump()
def reconciliation_to_dict(result): return result.model_dump()

def format_corporate_action_text(action): return f"{action.symbol} - {action.action_type.name} at {action.effective_date}"
def format_adjusted_price_result_text(result): return f"Adjusted {result.symbol}: {result.adjusted_rows} rows"
def format_reconciliation_text(result): return f"Reconciliation {result.symbol}: {result.mismatches} mismatches"
