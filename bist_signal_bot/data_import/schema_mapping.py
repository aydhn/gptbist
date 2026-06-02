from typing import Any
import pandas as pd
import uuid

from bist_signal_bot.data_import.models import (
    SchemaMapping,
    ColumnMapping,
    ImportDatasetType,
    ColumnSemanticType,
    ImportStatus,
)

class SchemaMappingEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def required_targets(self, dataset_type: ImportDatasetType) -> list[str]:
        if dataset_type == ImportDatasetType.OHLCV:
            return ["symbol", "date", "open", "high", "low", "close", "volume"]
        elif dataset_type == ImportDatasetType.FINANCIALS:
            return ["symbol", "period", "revenue", "net_income", "equity", "assets", "liabilities"]
        elif dataset_type == ImportDatasetType.MACRO:
            return ["date", "indicator", "value"]
        return []

    def suggest_target(self, source_column: str, dataset_type: ImportDatasetType) -> tuple[str | None, ColumnSemanticType]:
        col_lower = source_column.lower()

        # Base mapping
        if col_lower in ("symbol", "ticker", "sembol"):
            return "symbol", ColumnSemanticType.SYMBOL
        elif col_lower in ("date", "tarih", "timestamp", "time"):
            return "date", ColumnSemanticType.DATE
        elif col_lower in ("open", "açılış", "acilis"):
            return "open", ColumnSemanticType.OPEN
        elif col_lower in ("high", "yüksek", "yuksek"):
            return "high", ColumnSemanticType.HIGH
        elif col_lower in ("low", "düşük", "dusuk"):
            return "low", ColumnSemanticType.LOW
        elif col_lower in ("close", "kapanış", "kapanis"):
            return "close", ColumnSemanticType.CLOSE
        elif col_lower in ("volume", "hacim"):
            return "volume", ColumnSemanticType.VOLUME

        # Financials
        if dataset_type == ImportDatasetType.FINANCIALS:
            if col_lower in ("period", "dönem", "donem"):
                 return "period", ColumnSemanticType.DATE
            elif col_lower in ("revenue", "gelir", "satislar"):
                 return "revenue", ColumnSemanticType.NUMERIC
            elif col_lower in ("net_income", "net kar", "net_kar"):
                 return "net_income", ColumnSemanticType.NUMERIC
            elif col_lower in ("equity", "ozkaynaklar", "özkaynaklar"):
                 return "equity", ColumnSemanticType.NUMERIC
            elif col_lower in ("assets", "varliklar", "varlıklar", "toplam_varliklar"):
                 return "assets", ColumnSemanticType.NUMERIC
            elif col_lower in ("liabilities", "yukumlulukler", "yükümlülükler"):
                 return "liabilities", ColumnSemanticType.NUMERIC

        # Macro
        if dataset_type == ImportDatasetType.MACRO:
            if col_lower in ("indicator", "gosterge", "gösterge"):
                 return "indicator", ColumnSemanticType.CATEGORY
            elif col_lower in ("value", "deger", "değer"):
                 return "value", ColumnSemanticType.NUMERIC

        return None, ColumnSemanticType.UNKNOWN

    def infer_mapping(self, columns: list[str], dataset_type: ImportDatasetType) -> SchemaMapping:
        mappings = []
        unmapped = []
        mapped_targets = set()

        req_targets = self.required_targets(dataset_type)

        for col in columns:
            target, sem_type = self.suggest_target(col, dataset_type)
            if target:
                req = target in req_targets
                mappings.append(
                    ColumnMapping(
                        mapping_id=str(uuid.uuid4()),
                        source_column=col,
                        target_column=target,
                        semantic_type=sem_type,
                        required=req
                    )
                )
                mapped_targets.add(target)
            else:
                unmapped.append(col)

        missing_targets = [t for t in req_targets if t not in mapped_targets]

        status = ImportStatus.PASS if not missing_targets else ImportStatus.WATCH
        if missing_targets and self.settings and getattr(self.settings, "DATA_IMPORT_FAIL_ON_MISSING_REQUIRED", True):
             status = ImportStatus.FAIL

        mapping = SchemaMapping(
            schema_mapping_id=str(uuid.uuid4()),
            dataset_type=dataset_type,
            source_columns=columns,
            column_mappings=mappings,
            unmapped_columns=unmapped,
            missing_required_targets=missing_targets,
            status=status
        )

        mapping.confidence_score = self.mapping_confidence(mapping)
        return mapping

    def apply_mapping(self, df: pd.DataFrame, mapping: SchemaMapping) -> pd.DataFrame:
        rename_dict = {m.source_column: m.target_column for m in mapping.column_mappings}
        df_mapped = df.rename(columns=rename_dict)
        # Keep only mapped columns
        keep_cols = [m.target_column for m in mapping.column_mappings]
        # Only keep columns that actually exist in the DataFrame
        existing_keep_cols = [col for col in keep_cols if col in df_mapped.columns]
        return df_mapped[existing_keep_cols]

    def validate_mapping(self, mapping: SchemaMapping) -> list[str]:
        warnings = []
        if mapping.missing_required_targets:
            warnings.append(f"Missing required targets: {', '.join(mapping.missing_required_targets)}")
        if mapping.unmapped_columns:
             warnings.append(f"Unmapped columns: {', '.join(mapping.unmapped_columns)}")
        return warnings

    def mapping_confidence(self, mapping: SchemaMapping) -> float | None:
        if not mapping.source_columns:
            return 0.0
        mapped_ratio = len(mapping.column_mappings) / len(mapping.source_columns)

        req_targets = self.required_targets(mapping.dataset_type)
        if not req_targets:
             req_ratio = 1.0
        else:
             req_mapped = len([t for t in req_targets if t not in mapping.missing_required_targets])
             req_ratio = req_mapped / len(req_targets)

        return round((mapped_ratio * 0.4 + req_ratio * 0.6) * 100, 2)
