# Daily cost model and cash benchmark

Code: `edge_validation/costs_daily.py` (`DailyCostModel`), `edge_validation/cash_benchmark.py`.
Assumptions: capital 100,000 TL, long-only, no leverage. All rates are UNVERIFIED placeholders.

- Per leg bps: commission + BSMV(on commission only; 0 when commission 0, same as `IntradayCostModel`) + exchange fee
  + tick half-spread + sqrt impact `coef*100*sqrt(order/ADV)` (daily coef 0.5, ~11 bps at 5% ADV).
- NaN when participation > `DAILY_COST_MAX_PARTICIPATION` (5% ADV), ADV missing, short, or price-limit flag.
- `bar_value_try` = average daily value (TRY). Pass the model as `CandidateGate(cost_model=...)`.
- Always report two scenarios: `zero_commission` and `placeholder_commission`
  (`DAILY_COST_COMMISSION_PLACEHOLDER_BPS`=5 per leg): `DailyCostModel.from_settings(s, scenario=...)`.
- Cash benchmark: `CASH_BENCHMARK_ANNUAL_RATE`=0.37 (TCMB policy rate proxy), `CASH_BENCHMARK_WITHHOLDING`=0.0
  (gross). Separate from the deposit placeholder `PAPER_CASH_INTEREST_ANNUAL`=0.30 / withholding 0.15.
- Interest compounds over calendar days (weekend = 3 days). `holding_cost_bps` / `net_vs_cash` = interest forgone.
- `real_return` needs a CPI series; raises if missing (no CPI data yet).
