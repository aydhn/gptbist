from pathlib import Path
from typing import Any

from bist_signal_bot.data_catalog.models import (
    DatasetContract,
    DatasetFormat,
    DatasetKind,
)
from bist_signal_bot.config.settings import Settings, get_settings


class DatasetContractRegistry:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self._contracts: dict[str, DatasetContract] = {}
        if self.settings.DATA_CATALOG_LOAD_DEFAULT_CONTRACTS:
            self._load_defaults()

    def _load_defaults(self):
        for contract in self.default_contracts():
            self._contracts[contract.contract_id] = contract

    def _create_contract(self, kind: DatasetKind, required: list[str], optional: list[str] = None, date_cols: list[str] = None, formats: list[DatasetFormat] = None) -> DatasetContract:
        if optional is None:
             optional = []
        if date_cols is None:
             date_cols = []
        if formats is None:
             formats = [DatasetFormat.CSV, DatasetFormat.PARQUET]

        return DatasetContract(
            contract_id=f"contract_{kind.value.lower()}_{self.settings.DATA_CATALOG_CONTRACT_VERSION}",
            dataset_kind=kind,
            name=f"Default {kind.value} Contract",
            version=str(self.settings.DATA_CATALOG_CONTRACT_VERSION),
            required_columns=required,
            optional_columns=optional,
            date_columns=date_cols,
            allowed_formats=formats,
        )

    def default_contracts(self) -> list[DatasetContract]:
        return [
            self._create_contract(
                DatasetKind.OHLCV,
                ["symbol", "date", "open", "high", "low", "close", "volume"],
                ["adj_close"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.ADJUSTED_OHLCV,
                ["symbol", "date", "open", "high", "low", "close", "volume"],
                [],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.INSTRUMENTS,
                ["symbol", "name", "sector", "currency"],
                ["isin", "market_cap"],
                []
            ),
            self._create_contract(
                DatasetKind.CORPORATE_ACTIONS,
                ["symbol", "date", "action_type"],
                ["value", "ratio"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.EVENTS,
                ["symbol", "date", "event_type"],
                ["title", "description"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.DISCLOSURES,
                ["symbol", "date", "title", "link"],
                ["content", "summary"],
                ["date"],
                [DatasetFormat.CSV, DatasetFormat.JSONL]
            ),
            self._create_contract(
                DatasetKind.FINANCIALS,
                ["symbol", "period_end_date", "revenue", "net_income"],
                ["ebitda", "total_assets", "total_liabilities"],
                ["period_end_date"]
            ),
            self._create_contract(
                DatasetKind.MACRO,
                ["date", "indicator_name", "value"],
                ["region"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.VALUATION,
                ["symbol", "date", "pe_ratio", "pb_ratio"],
                ["ev_ebitda", "dividend_yield"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.FACTORS,
                ["symbol", "date", "factor_name", "factor_score"],
                [],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.BREADTH,
                ["date", "market_regime", "advancing", "declining"],
                ["new_highs", "new_lows"],
                ["date"]
            ),
            self._create_contract(
                DatasetKind.CONTEXT,
                ["date", "symbol", "context_summary"],
                ["evidence_gap"],
                ["date"],
                [DatasetFormat.JSON, DatasetFormat.JSONL]
            ),
            self._create_contract(
                DatasetKind.REVIEW_WORKFLOW,
                ["case_id", "created_at", "status"],
                ["resolution", "reviewer"],
                ["created_at"],
                [DatasetFormat.JSON, DatasetFormat.JSONL]
            ),
            self._create_contract(
                DatasetKind.QA,
                ["run_id", "timestamp", "status", "coverage"],
                ["failures"],
                ["timestamp"],
                [DatasetFormat.JSON, DatasetFormat.JSONL]
            ),
            self._create_contract(
                DatasetKind.OPS,
                ["timestamp", "component", "status"],
                ["latency", "error_rate"],
                ["timestamp"],
                [DatasetFormat.JSON, DatasetFormat.JSONL]
            ),
            self._create_contract(
                DatasetKind.REPORTS,
                ["date", "report_type", "content"],
                [],
                ["date"],
                [DatasetFormat.MARKDOWN, DatasetFormat.JSON]
            ),
        ]

    def get_contract(self, dataset_kind: DatasetKind | str) -> DatasetContract | None:
        if isinstance(dataset_kind, str):
            try:
                dataset_kind = DatasetKind(dataset_kind.upper())
            except ValueError:
                return None

        for contract in self._contracts.values():
            if contract.dataset_kind == dataset_kind:
                return contract
        return None

    def validate_contract(self, contract: DatasetContract) -> list[str]:
        errors = []
        if not contract.required_columns:
            errors.append("Contract must specify at least one required column.")
        if contract.dataset_kind not in DatasetKind:
            errors.append(f"Invalid dataset kind: {contract.dataset_kind}")
        return errors

    _PATH_MAPPING = (
        (["adjusted_ohlcv"], DatasetKind.ADJUSTED_OHLCV),
        (["instrument", "symbols"], DatasetKind.INSTRUMENTS),
        (["corporate", "actions"], DatasetKind.CORPORATE_ACTIONS),
        (["event"], DatasetKind.EVENTS),
        (["disclosure", "kap"], DatasetKind.DISCLOSURES),
        (["financial", "balance_sheet", "income_statement"], DatasetKind.FINANCIALS),
        (["macro"], DatasetKind.MACRO),
        (["valuation"], DatasetKind.VALUATION),
        (["factor"], DatasetKind.FACTORS),
        (["breadth"], DatasetKind.BREADTH),
        (["context"], DatasetKind.CONTEXT),
        (["review"], DatasetKind.REVIEW_WORKFLOW),
        (["qa"], DatasetKind.QA),
        (["ops"], DatasetKind.OPS),
        (["report"], DatasetKind.REPORTS),
    )

    def contract_for_path(self, path: Path) -> DatasetContract | None:
        name = path.name.lower()
        if "ohlcv" in name and "adjusted" not in name:
            return self.get_contract(DatasetKind.OHLCV)

        for keywords, kind in self._PATH_MAPPING:
            if any(k in name for k in keywords):
                return self.get_contract(kind)

        return None

    def safe_contract_summary(self, contract: DatasetContract) -> dict[str, Any]:
        return {
            "contract_id": contract.contract_id,
            "dataset_kind": contract.dataset_kind.value,
            "version": contract.version,
            "required_columns_count": len(contract.required_columns),
            "date_columns_count": len(contract.date_columns),
            "disclaimer": contract.disclaimer
        }
