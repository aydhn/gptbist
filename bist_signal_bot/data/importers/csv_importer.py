import pandas as pd
from pathlib import Path
from typing import Optional
from bist_signal_bot.data.providers_v2.models import ImportRequest, ImportResult, DataImportStatus, DataLineageSource, ProviderType
from bist_signal_bot.data.importers.normalizer import ImportedDataNormalizer
import uuid
from datetime import datetime

class CSVMarketDataImporter:
    def __init__(self, normalizer: Optional[ImportedDataNormalizer] = None):
        self.normalizer = normalizer or ImportedDataNormalizer()

    def read_csv(self, path: Path, delimiter: Optional[str] = None) -> pd.DataFrame:
        try:
            if delimiter:
                return pd.read_csv(path, sep=delimiter)
            return pd.read_csv(path)
        except Exception as e:
            from bist_signal_bot.core.exceptions import DataImportError
            raise DataImportError(f"Failed to read CSV file {path}: {e}")

    def infer_symbol_from_filename(self, path: Path) -> Optional[str]:
        return path.stem.upper()

    def import_file(self, request: ImportRequest) -> ImportResult:
        warnings = []
        errors = []
        status = DataImportStatus.IMPORTED
        lineage = None

        path = Path(request.input_path)
        if not path.exists():
            return ImportResult(
                request=request,
                status=DataImportStatus.FAILED,
                symbol=request.symbol or "UNKNOWN",
                timeframe=request.timeframe,
                errors=[f"File not found: {path}"]
            )

        symbol = request.symbol or self.infer_symbol_from_filename(path)
        if not symbol:
             return ImportResult(
                request=request,
                status=DataImportStatus.FAILED,
                symbol="UNKNOWN",
                timeframe=request.timeframe,
                errors=["Could not infer symbol from filename and no symbol provided."]
            )

        try:
            df = self.read_csv(path, request.delimiter)
            if df.empty:
                return ImportResult(
                    request=request,
                    status=DataImportStatus.FAILED,
                    symbol=symbol,
                    timeframe=request.timeframe,
                    errors=["CSV file is empty."]
                )

            df = self.normalizer.normalize_ohlcv(df, request.column_mapping)

            missing = self.normalizer.validate_required_columns(df)
            if missing:
                return ImportResult(
                    request=request,
                    status=DataImportStatus.VALIDATION_FAILED,
                    symbol=symbol,
                    timeframe=request.timeframe,
                    errors=[f"Missing required columns after normalization: {missing}"]
                )

            lineage = DataLineageSource(
                source_id=str(uuid.uuid4()),
                provider_type=ProviderType.LOCAL_FILE,
                provider_name="CSV Importer",
                symbol=symbol,
                timeframe=request.timeframe,
                start_date=df['date'].min(),
                end_date=df['date'].max(),
                fetched_at=datetime.utcnow(),
                row_count=len(df),
                source_path=str(path)
            )

        except Exception as e:
            return ImportResult(
                request=request,
                status=DataImportStatus.FAILED,
                symbol=symbol,
                timeframe=request.timeframe,
                errors=[str(e)]
            )

        metadata = request.metadata.copy()
        metadata["_parsed_df"] = df

        return ImportResult(
            request=request,
            status=status,
            symbol=symbol,
            timeframe=request.timeframe,
            rows_imported=len(df),
            lineage=lineage,
            warnings=warnings,
            errors=errors,
            metadata=metadata
        )
