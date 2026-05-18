import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

class IncrementalUpdatePlanner:
    def plan_update(self, symbol: str, timeframe: str, local_data: Optional[pd.DataFrame], target_end: Optional[datetime] = None) -> Dict[str, Any]:
        target_end = target_end or datetime.utcnow()

        if local_data is None or local_data.empty or 'date' not in local_data.columns:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "action": "FULL_FETCH",
                "start_date": None,
                "end_date": target_end,
                "reason": "No local data found"
            }

        last_date = local_data['date'].max()
        lookback_days = 5
        start_date = last_date - timedelta(days=lookback_days)

        if start_date >= target_end:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "action": "SKIP",
                "start_date": None,
                "end_date": None,
                "reason": "Local data is up to date"
            }

        missing_dates = self.detect_missing_dates(local_data, timeframe)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "action": "INCREMENTAL_FETCH",
            "start_date": start_date,
            "end_date": target_end,
            "missing_gaps": missing_dates,
            "reason": f"Update needed from {start_date.date()}"
        }

    def detect_missing_dates(self, data: pd.DataFrame, timeframe: str) -> List[datetime]:
        if data is None or data.empty or 'date' not in data.columns:
            return []

        dates = pd.to_datetime(data['date']).sort_values().reset_index(drop=True)
        gaps = []

        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            if diff > 3:
                gaps.append(dates[i-1] + timedelta(days=1))

        return gaps

    def merge_incremental_data(self, existing: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        if new_data is None or new_data.empty:
            return existing
        if existing is None or existing.empty:
            return new_data

        merged = pd.concat([existing, new_data], ignore_index=True)
        if 'date' in merged.columns:
            merged.sort_values('date', inplace=True)
            merged.drop_duplicates(subset=['date'], keep='last', inplace=True)
            merged.reset_index(drop=True, inplace=True)

        return merged

    def should_update(self, latest_date: Optional[datetime], max_age_hours: float) -> bool:
        if not latest_date:
            return True
        age = (datetime.utcnow().replace(tzinfo=None) - latest_date.replace(tzinfo=None)).total_seconds() / 3600
        return age > max_age_hours
