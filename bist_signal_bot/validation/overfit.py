from bist_signal_bot.validation.models import OverfitRiskLevel, RobustnessResult, WalkForwardResult


class OverfitRiskAnalyzer:
    def __init__(self, degradation_warning_pct: float = 50.0, min_trades_per_split: int = 3):
        self.degradation_warning_pct = degradation_warning_pct
        self.min_trades_per_split = min_trades_per_split

    def assess_walk_forward(self, result: WalkForwardResult) -> tuple[OverfitRiskLevel, list[str]]:
        warnings = []
        if not result.split_results:
            return OverfitRiskLevel.UNKNOWN, ["No split results available."]

        if len(result.split_results) == 1:
            warnings.append("Only one split evaluated, risk assessment is limited.")

        negative_splits = 0
        total_splits = len(result.split_results)
        large_degradations = 0
        low_trades = 0

        for sr in result.split_results:
            test_ret = sr.test_report.return_metrics.total_return_pct
            if test_ret < 0:
                negative_splits += 1

            if sr.test_report.trade_metrics.trade_count < self.min_trades_per_split:
                low_trades += 1

            if sr.train_report:
                train_ret = sr.train_report.return_metrics.total_return_pct
                if train_ret > 0 and test_ret < train_ret:
                    degradation = ((train_ret - test_ret) / train_ret) * 100
                    if degradation > self.degradation_warning_pct:
                        large_degradations += 1

        if negative_splits > total_splits / 2:
            warnings.append(
                f"Majority of test splits ({negative_splits}/{total_splits}) are negative."
            )
        if large_degradations > 0:
            warnings.append(
                f"{large_degradations} splits showed >{self.degradation_warning_pct}% return degradation from train to test."  # noqa: E501
            )
        if low_trades > 0:
            warnings.append(
                f"{low_trades} splits had fewer than {self.min_trades_per_split} trades."
            )

        if negative_splits > total_splits / 2 or large_degradations > total_splits / 2:
            level = OverfitRiskLevel.HIGH
        elif negative_splits > 0 or large_degradations > 0 or low_trades > 0:
            level = OverfitRiskLevel.MEDIUM
        else:
            level = OverfitRiskLevel.LOW

        if total_splits == 1 and level == OverfitRiskLevel.LOW:
            level = OverfitRiskLevel.UNKNOWN

        return level, warnings

    def assess_robustness(self, result: RobustnessResult) -> tuple[OverfitRiskLevel, list[str]]:
        warnings = []
        if not result.run_results:
            return OverfitRiskLevel.UNKNOWN, ["No robustness runs available."]

        if len(result.run_results) < 5:
            warnings.append("Too few runs for a confident robustness assessment.")

        if result.stability_score < 40.0:
            warnings.append(
                f"Low stability score ({result.stability_score:.2f}). Parameter changes cause high variance."  # noqa: E501
            )

        negative_runs = sum(
            1
            for r in result.run_results
            if (r.performance_report.return_metrics.total_return_pct or 0.0) < 0
        )
        total_runs = len(result.run_results)

        if negative_runs > total_runs * 0.75:
            warnings.append(
                f"Over 75% of parameter combinations ({negative_runs}/{total_runs}) resulted in negative returns."  # noqa: E501
            )

        if result.stability_score < 30.0 or negative_runs > total_runs * 0.75:
            level = OverfitRiskLevel.HIGH
        elif result.stability_score < 50.0 or negative_runs > total_runs * 0.4:
            level = OverfitRiskLevel.MEDIUM
        else:
            level = OverfitRiskLevel.LOW

        if total_runs < 5 and level == OverfitRiskLevel.LOW:
            level = OverfitRiskLevel.UNKNOWN

        return level, warnings
