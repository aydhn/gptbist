import pandas as pd
from typing import Optional, Dict, List

class ImportedDataNormalizer:
    def standard_columns(self) -> List[str]:
        return ['date', 'open', 'high', 'low', 'close', 'volume']

    def normalize_ohlcv(self, df: pd.DataFrame, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        df = df.copy()

        df.columns = [str(c).lower() for c in df.columns]

        if column_mapping:
            lower_map = {k.lower(): v.lower() for k, v in column_mapping.items()}
            df.rename(columns=lower_map, inplace=True)

        tr_map = {
            'tarih': 'date',
            'datetime': 'date',
            'açılış': 'open',
            'acilis': 'open',
            'yüksek': 'high',
            'yuksek': 'high',
            'düşük': 'low',
            'dusuk': 'low',
            'kapanış': 'close',
            'kapanis': 'close',
            'hacim': 'volume'
        }
        df.rename(columns=tr_map, inplace=True)

        df = self.normalize_date_column(df)

        df = self.sort_and_deduplicate(df)

        cols_to_keep = [c for c in self.standard_columns() if c in df.columns]
        df = df[cols_to_keep]

        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def validate_required_columns(self, df: pd.DataFrame) -> List[str]:
        missing = []
        for col in self.standard_columns():
            if col not in df.columns:
                missing.append(col)
        return missing

    def normalize_date_column(self, df: pd.DataFrame, date_column: Optional[str] = None) -> pd.DataFrame:
        col = date_column or 'date'
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            df.dropna(subset=[col], inplace=True)
            df[col] = df[col].dt.tz_localize(None)
        return df

    def sort_and_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'date' in df.columns:
            df.sort_values('date', inplace=True)
            df.drop_duplicates(subset=['date'], keep='last', inplace=True)
            df.reset_index(drop=True, inplace=True)
        return df
