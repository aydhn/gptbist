import uuid
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import (
    ValuationMetricType, ValuationStatus, PeerValuationComparison, ValuationMultiple
)

class PeerValuationComparator:
    def __init__(self, settings: Optional[Settings] = None, instrument_master: Any = None):
        self.settings = settings or Settings()
        self.instrument_master = instrument_master
        self.min_peers = getattr(self.settings, "VALUATION_MIN_PEER_COUNT", 3)
        self.use_sector = getattr(self.settings, "VALUATION_USE_SECTOR_PEERS", True)

    def peer_group(self, symbol: str) -> List[str]:
        if not self.use_sector or not self.instrument_master:
            return []

        record = self.instrument_master.get(symbol)
        if not record:
            return []

        sector = getattr(record, "sector", None)
        if not sector:
            return []

        peers = []
        # Fallback pseudo-code, assumes instrument_master can be iterated
        if hasattr(self.instrument_master, "_records"):
            for p_sym, p_rec in self.instrument_master._records.items():
                if getattr(p_rec, "sector", None) == sector and p_sym != symbol:
                    peers.append(p_sym)
        return peers

    def peer_values(self, metric_type: ValuationMetricType, peers: List[str], multiples_by_symbol: Dict[str, List[ValuationMultiple]]) -> List[float]:
        values = []
        for peer in peers:
            # Get latest valid multiple for this peer and metric
            peer_mults = multiples_by_symbol.get(peer, [])
            valid_mults = [m for m in peer_mults if m.metric_type == metric_type and m.value is not None]
            if valid_mults:
                # Assuming sorted or taking the latest
                latest = sorted(valid_mults, key=lambda x: x.as_of)[-1]
                values.append(latest.value)
        return values

    def relative_discount_premium(self, subject_value: Optional[float], peer_median: Optional[float]) -> Optional[float]:
        if subject_value is None or peer_median is None or peer_median == 0:
            return None
        # Negative means discount (cheaper), positive means premium (more expensive)
        return ((subject_value - peer_median) / abs(peer_median)) * 100.0

    def classify_relative(self, percentile_rank: Optional[float], discount_premium_pct: Optional[float]) -> ValuationStatus:
        if percentile_rank is None:
            return ValuationStatus.INSUFFICIENT_DATA

        if percentile_rank <= 10.0:
            return ValuationStatus.EXTREME_CHEAP
        elif percentile_rank <= 25.0:
            return ValuationStatus.CHEAP
        elif percentile_rank >= 90.0:
            return ValuationStatus.EXTREME_EXPENSIVE
        elif percentile_rank >= 75.0:
            return ValuationStatus.EXPENSIVE
        else:
            return ValuationStatus.FAIR

    def compare_symbol(self, symbol: str, metric_type: ValuationMetricType, multiples_by_symbol: Dict[str, List[ValuationMultiple]]) -> PeerValuationComparison:
        warnings = []
        subject_mults = multiples_by_symbol.get(symbol, [])
        valid_subject = [m for m in subject_mults if m.metric_type == metric_type and m.value is not None]

        subject_value = None
        as_of = datetime.utcnow()
        if valid_subject:
            latest = sorted(valid_subject, key=lambda x: x.as_of)[-1]
            subject_value = latest.value
            as_of = latest.as_of

        peers = self.peer_group(symbol)
        p_values = self.peer_values(metric_type, peers, multiples_by_symbol)

        sector = None
        if self.instrument_master:
            rec = self.instrument_master.get(symbol)
            if rec: sector = getattr(rec, "sector", None)

        if len(p_values) < self.min_peers:
            warnings.append(f"Insufficient peers for {metric_type.value}. Found {len(p_values)}, minimum is {self.min_peers}.")
            return PeerValuationComparison(
                comparison_id=str(uuid.uuid4()),
                symbol=symbol,
                sector=sector,
                as_of=as_of,
                metric_type=metric_type,
                subject_value=subject_value,
                peer_count=len(p_values),
                status=ValuationStatus.INSUFFICIENT_DATA,
                warnings=warnings
            )

        peer_median = float(np.median(p_values))
        peer_average = float(np.mean(p_values))

        # Calculate rank
        all_values = p_values + ([subject_value] if subject_value is not None else [])
        all_values.sort()

        percentile_rank = None
        if subject_value is not None:
             count_below = sum(1 for v in p_values if v < subject_value)
             count_equal = sum(1 for v in p_values if v == subject_value)
             percentile_rank = ((count_below + 0.5 * count_equal) / len(p_values)) * 100.0

        discount_prem = self.relative_discount_premium(subject_value, peer_median)
        status = self.classify_relative(percentile_rank, discount_prem)

        # Reverse logic for yields
        if metric_type in [ValuationMetricType.FCF_YIELD, ValuationMetricType.EARNINGS_YIELD, ValuationMetricType.DIVIDEND_YIELD]:
             if status == ValuationStatus.EXTREME_CHEAP: status = ValuationStatus.EXTREME_EXPENSIVE
             elif status == ValuationStatus.CHEAP: status = ValuationStatus.EXPENSIVE
             elif status == ValuationStatus.EXPENSIVE: status = ValuationStatus.CHEAP
             elif status == ValuationStatus.EXTREME_EXPENSIVE: status = ValuationStatus.EXTREME_CHEAP

             if percentile_rank is not None:
                 percentile_rank = 100.0 - percentile_rank

             if discount_prem is not None:
                 discount_prem = -discount_prem

        return PeerValuationComparison(
            comparison_id=str(uuid.uuid4()),
            symbol=symbol,
            sector=sector,
            as_of=as_of,
            metric_type=metric_type,
            subject_value=subject_value,
            peer_median=peer_median,
            peer_average=peer_average,
            peer_percentile_rank=percentile_rank,
            peer_count=len(p_values),
            relative_discount_premium_pct=discount_prem,
            status=status,
            warnings=warnings
        )
