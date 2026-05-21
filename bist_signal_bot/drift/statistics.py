import math
import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

class DriftStatistics:
    @staticmethod
    def safe_numeric_series(values: list[Any]) -> list[float]:
        result = []
        for v in values:
            try:
                if v is not None and not math.isnan(float(v)) and not math.isinf(float(v)):
                    result.append(float(v))
            except (ValueError, TypeError):
                continue
        return result

    @staticmethod
    def population_stability_index(reference: list[float], current: list[float], bins: int = 10) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)

        if len(ref) == 0 or len(cur) == 0:
            return None

        min_val = min(min(ref), min(cur))
        max_val = max(max(ref), max(cur))

        if min_val == max_val:
            return 0.0

        bin_edges = np.linspace(min_val, max_val, bins + 1)
        ref_counts, _ = np.histogram(ref, bins=bin_edges)
        cur_counts, _ = np.histogram(cur, bins=bin_edges)

        epsilon = 0.0001
        ref_pct = (ref_counts / len(ref)) + epsilon
        cur_pct = (cur_counts / len(cur)) + epsilon

        ref_pct = ref_pct / np.sum(ref_pct)
        cur_pct = cur_pct / np.sum(cur_pct)

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi)

    @staticmethod
    def ks_statistic(reference: list[float], current: list[float]) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)

        if len(ref) == 0 or len(cur) == 0:
            return None

        try:
            from scipy.stats import ks_2samp
            stat, _ = ks_2samp(ref, cur)
            return float(stat)
        except ImportError:
            data1 = np.sort(ref)
            data2 = np.sort(cur)
            n1 = len(data1)
            n2 = len(data2)

            data_all = np.concatenate([data1, data2])
            cdf1 = np.searchsorted(data1, data_all, side='right') / n1
            cdf2 = np.searchsorted(data2, data_all, side='right') / n2

            return float(np.max(np.abs(cdf1 - cdf2)))

    @staticmethod
    def wasserstein_distance(reference: list[float], current: list[float]) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)

        if len(ref) == 0 or len(cur) == 0:
            return None

        try:
            from scipy.stats import wasserstein_distance
            return float(wasserstein_distance(ref, cur))
        except ImportError:
            data1 = np.sort(ref)
            data2 = np.sort(cur)
            quantiles = np.linspace(0, 1, 100)
            q1 = np.quantile(data1, quantiles)
            q2 = np.quantile(data2, quantiles)
            return float(np.mean(np.abs(q1 - q2)))

    @staticmethod
    def mean_shift(reference: list[float], current: list[float]) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)
        if len(ref) == 0 or len(cur) == 0:
            return None
        return float(np.mean(cur) - np.mean(ref))

    @staticmethod
    def std_shift(reference: list[float], current: list[float]) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)
        if len(ref) == 0 or len(cur) == 0:
            return None
        return float(np.std(cur) - np.std(ref))

    @staticmethod
    def quantile_shift(reference: list[float], current: list[float], q: float) -> float | None:
        ref = DriftStatistics.safe_numeric_series(reference)
        cur = DriftStatistics.safe_numeric_series(current)
        if len(ref) == 0 or len(cur) == 0:
            return None
        return float(np.quantile(cur, q) - np.quantile(ref, q))

    @staticmethod
    def rate_change(reference_rate: float | None, current_rate: float | None) -> float | None:
        if reference_rate is None or current_rate is None:
            return None
        if reference_rate == 0:
            return 0.0 if current_rate == 0 else float('inf')
        return float(((current_rate - reference_rate) / abs(reference_rate)) * 100)
