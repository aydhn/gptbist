import logging
import time
from datetime import date, datetime, UTC
from typing import Any

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PriceAdjustmentError
from bist_signal_bot.data.corporate_actions import CorporateActionStore
from bist_signal_bot.data.models import (
    AdjustedMarketData,
    AdjustmentIssue,
    AdjustmentPolicy,
    AdjustmentReport,
    AdjustmentStatus,
    CorporateAction,
    CorporateActionType,
    MarketDataFrame,
)

logger = logging.getLogger("bist_signal_bot.data.adjustments")


class PriceAdjustmentEngine:
    def __init__(
        self,
        settings: Settings | None = None,
        action_store: CorporateActionStore | None = None,
        policy: AdjustmentPolicy = AdjustmentPolicy.FLAG_ONLY,
        apply_to_ohlc: bool = True,
        apply_to_volume: bool = True,
        require_verified_actions: bool = False,
        strict: bool = True
    ):
        self.settings = settings
        self.action_store = action_store
        self.policy = policy
        self.apply_to_ohlc = apply_to_ohlc
        self.apply_to_volume = apply_to_volume
        self.require_verified_actions = require_verified_actions
        self.strict = strict

    def build_report(
        self,
        symbol: str,
        timeframe: str,
        source: str,
        status: AdjustmentStatus,
        input_rows: int,
        output_rows: int,
        actions_available: int,
        actions_applied: int,
        adjusted_columns: list[str],
        volume_adjusted: bool,
        issues: list[AdjustmentIssue],
        start_time: datetime,
        end_time: datetime
    ) -> AdjustmentReport:
        return AdjustmentReport(
            symbol=symbol,
            timeframe=timeframe,
            source=source,
            policy=self.policy,
            status=status,
            input_rows=input_rows,
            output_rows=output_rows,
            actions_available=actions_available,
            actions_applied=actions_applied,
            adjusted_columns=adjusted_columns,
            volume_adjusted=volume_adjusted,
            issues=issues,
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=(end_time - start_time).total_seconds()
        )

    def apply_split_adjustments(self, df: pd.DataFrame, actions: list[CorporateAction]) -> tuple[pd.DataFrame, list[AdjustmentIssue]]:
        issues = []
        df_adj = df.copy()

        # Ensure index is datetime and localized (or at least comparable to date)
        if not isinstance(df_adj.index, pd.DatetimeIndex):
            issues.append(AdjustmentIssue(
                issue_type="INVALID_INDEX",
                message="DataFrame index is not DatetimeIndex, cannot apply date-based adjustments."
            ))
            return df_adj, issues

        split_types = [CorporateActionType.SPLIT, CorporateActionType.REVERSE_SPLIT, CorporateActionType.BONUS_ISSUE]

        # Sort actions descending so we apply the most recent split first
        split_actions = sorted([a for a in actions if a.action_type in split_types], key=lambda x: x.action_date, reverse=True)

        for action in split_actions:
            if action.ratio is None or action.ratio <= 0:
                issues.append(AdjustmentIssue(
                    issue_type="INVALID_RATIO",
                    message=f"Invalid or missing ratio for action on {action.action_date}.",
                    action_date=action.action_date,
                    action_type=action.action_type
                ))
                continue

            # For standard SPLIT and BONUS_ISSUE, factor = ratio (e.g. 2 means 2-for-1). Prices divide by 2, Volume multiplies by 2.
            # For REVERSE_SPLIT, typically ratio is also expressed > 1 (e.g. 1-for-10 means ratio=10). Prices multiply by 10, Volume divides by 10.
            # Let's define the multiplier:
            if action.action_type == CorporateActionType.REVERSE_SPLIT:
                price_mult = action.ratio
                vol_mult = 1.0 / action.ratio
            else:
                price_mult = 1.0 / action.ratio
                vol_mult = action.ratio

            action_date_dt = pd.to_datetime(action.action_date).tz_localize(df_adj.index.tz) if df_adj.index.tz else pd.to_datetime(action.action_date)

            # Mask for strictly BEFORE the action date
            mask = df_adj.index < action_date_dt

            affected = mask.sum()
            if affected == 0:
                issues.append(AdjustmentIssue(
                    issue_type="NO_ROWS_AFFECTED",
                    message=f"Action date {action.action_date} is before the first row of data or not present.",
                    action_date=action.action_date,
                    action_type=action.action_type
                ))
                continue

            cols_adj = []
            if self.apply_to_ohlc:
                for col in ["open", "high", "low", "close"]:
                    if col in df_adj.columns:
                        df_adj.loc[mask, col] = df_adj.loc[mask, col] * price_mult
                        cols_adj.append(col)

            if self.apply_to_volume and "volume" in df_adj.columns:
                df_adj.loc[mask, "volume"] = df_adj.loc[mask, "volume"] * vol_mult
                cols_adj.append("volume")

            issues.append(AdjustmentIssue(
                issue_type="APPLIED_SPLIT",
                message=f"Applied {action.action_type.value} adjustment (ratio: {action.ratio}).",
                affected_rows=int(affected),
                action_date=action.action_date,
                action_type=action.action_type,
                metadata={"price_multiplier": price_mult, "volume_multiplier": vol_mult, "adjusted_columns": cols_adj}
            ))

        return df_adj, issues

    def apply_provider_adjusted(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[AdjustmentIssue]]:
        issues = []
        df_adj = df.copy()

        if "adj_close" not in df_adj.columns or "close" not in df_adj.columns:
            issues.append(AdjustmentIssue(
                issue_type="MISSING_ADJ_CLOSE",
                message="Cannot apply USE_PROVIDER_ADJUSTED because 'adj_close' or 'close' column is missing."
            ))
            return df_adj, issues

        # Calculate adjustment factor. To avoid div by zero:
        factor = df_adj['adj_close'] / df_adj['close'].replace(0, pd.NA)

        # Fill missing factors with 1.0 (no adjustment)
        factor = factor.fillna(1.0)

        affected = (factor != 1.0).sum()

        if affected == 0:
            issues.append(AdjustmentIssue(
                issue_type="NO_ADJUSTMENT_NEEDED",
                message="Provider 'adj_close' equals 'close' for all rows. No adjustment applied."
            ))
            return df_adj, issues

        cols_adj = []
        if self.apply_to_ohlc:
            for col in ["open", "high", "low", "close"]:
                if col in df_adj.columns:
                    df_adj[col] = df_adj[col] * factor
                    cols_adj.append(col)

        # Generally providers don't adjust volume with adj_close, but if requested:
        if self.apply_to_volume and "volume" in df_adj.columns:
            # Volume usually inversely proportional to price factor
            df_adj["volume"] = df_adj["volume"] / factor.replace(0, pd.NA).fillna(1.0)
            cols_adj.append("volume")

        issues.append(AdjustmentIssue(
            issue_type="APPLIED_PROVIDER_ADJUSTED",
            message=f"Applied provider adjusted close factor.",
            affected_rows=int(affected),
            metadata={"adjusted_columns": cols_adj}
        ))

        return df_adj, issues

    def detect_potential_unadjusted_events(self, df: pd.DataFrame) -> list[AdjustmentIssue]:
        issues = []
        if "close" not in df.columns or len(df) < 2:
            return issues

        returns = df["close"].pct_change().abs()
        # threshold 20%
        extreme_mask = returns > 0.20
        extreme_dates = df.index[extreme_mask]

        for dt in extreme_dates:
            issues.append(AdjustmentIssue(
                issue_type="POTENTIAL_UNADJUSTED_EVENT",
                message=f"Extreme return detected ({returns[dt]:.2%}). Potential unadjusted corporate action.",
                action_date=dt.date(),
                affected_rows=1
            ))

        return issues

    def adjust_market_data(self, market_data: MarketDataFrame) -> AdjustedMarketData:
        start_time = datetime.now(UTC)
        symbol = market_data.symbol

        input_df = market_data.data.copy()
        input_rows = len(input_df)

        issues = []
        actions = []

        if self.action_store and self.action_store.exists():
            all_actions = self.action_store.get_actions_for_symbol(symbol)
            if self.require_verified_actions:
                actions = [a for a in all_actions if a.verified]
            else:
                actions = all_actions

        actions_available = len(actions)
        actions_applied = 0
        adjusted_columns = []
        volume_adjusted = False

        df_adj = input_df.copy()

        status = AdjustmentStatus.SUCCESS

        try:
            if self.policy == AdjustmentPolicy.NONE:
                status = AdjustmentStatus.SKIPPED
                issues.append(AdjustmentIssue(issue_type="POLICY_NONE", message="Adjustment policy is NONE. Skipped."))

            elif self.policy == AdjustmentPolicy.FLAG_ONLY:
                status = AdjustmentStatus.SUCCESS
                issues.append(AdjustmentIssue(issue_type="FLAG_ONLY", message="Policy is FLAG_ONLY. No data modified."))
                # Flag potential unadjusted events
                issues.extend(self.detect_potential_unadjusted_events(df_adj))

            elif self.policy == AdjustmentPolicy.USE_PROVIDER_ADJUSTED:
                df_adj, applied_issues = self.apply_provider_adjusted(df_adj)
                issues.extend(applied_issues)
                if any(i.issue_type == "MISSING_ADJ_CLOSE" for i in applied_issues):
                    status = AdjustmentStatus.SKIPPED if not self.strict else AdjustmentStatus.WARNING
                else:
                    actions_applied = 1 # Logical flag
                    if self.apply_to_ohlc: adjusted_columns.extend(["open", "high", "low", "close"])
                    if self.apply_to_volume:
                        adjusted_columns.append("volume")
                        volume_adjusted = True

            elif self.policy == AdjustmentPolicy.MANUAL_SPLIT_ADJUST:
                df_adj, applied_issues = self.apply_split_adjustments(df_adj, actions)
                issues.extend(applied_issues)
                applied_count = sum(1 for i in applied_issues if i.issue_type == "APPLIED_SPLIT")
                actions_applied = applied_count
                if applied_count > 0:
                    if self.apply_to_ohlc: adjusted_columns.extend(["open", "high", "low", "close"])
                    if self.apply_to_volume:
                        adjusted_columns.append("volume")
                        volume_adjusted = True

            elif self.policy == AdjustmentPolicy.MANUAL_DIVIDEND_ADJUST:
                status = AdjustmentStatus.SKIPPED
                issues.append(AdjustmentIssue(
                    issue_type="UNSUPPORTED_POLICY",
                    message="MANUAL_DIVIDEND_ADJUST is not implemented in this phase. Skipping."
                ))

            elif self.policy == AdjustmentPolicy.MANUAL_TOTAL_RETURN:
                if self.strict:
                    raise PriceAdjustmentError("MANUAL_TOTAL_RETURN is not supported in Phase 15.")
                else:
                    status = AdjustmentStatus.FAILED
                    issues.append(AdjustmentIssue(
                        issue_type="UNSUPPORTED_POLICY",
                        message="MANUAL_TOTAL_RETURN is not supported. Failed."
                    ))

            # Deduplicate adjusted_columns
            adjusted_columns = list(set([c for c in adjusted_columns if c in df_adj.columns]))

        except Exception as e:
            logger.error(f"Error adjusting data for {symbol}: {e}", exc_info=True)
            status = AdjustmentStatus.FAILED
            issues.append(AdjustmentIssue(
                issue_type="INTERNAL_ERROR",
                message=f"Internal error during adjustment: {e}"
            ))
            if self.strict and self.policy != AdjustmentPolicy.NONE and self.policy != AdjustmentPolicy.FLAG_ONLY:
                raise PriceAdjustmentError(f"Adjustment failed for {symbol}: {e}")

        end_time = datetime.now(UTC)

        report = self.build_report(
            symbol=symbol,
            timeframe=market_data.timeframe.value,
            source=market_data.source.value,
            status=status,
            input_rows=input_rows,
            output_rows=len(df_adj),
            actions_available=actions_available,
            actions_applied=actions_applied,
            adjusted_columns=adjusted_columns,
            volume_adjusted=volume_adjusted,
            issues=issues,
            start_time=start_time,
            end_time=end_time
        )

        # Build new MarketDataFrame
        new_metadata = dict(market_data.metadata)
        new_metadata.update({
            "adjusted_by_engine": True if actions_applied > 0 or self.policy == AdjustmentPolicy.USE_PROVIDER_ADJUSTED else False,
            "adjustment_policy": self.policy.value,
            "adjustment_status": status.value,
            "actions_available": actions_available,
            "actions_applied": actions_applied,
            "adjusted_columns": adjusted_columns,
            "volume_adjusted": volume_adjusted,
            "adjustment_issue_count": len(issues)
        })

        # Do not alter original adjusted boolean unless we truly adjusted
        final_adjusted = market_data.adjusted
        if self.policy in [AdjustmentPolicy.MANUAL_SPLIT_ADJUST, AdjustmentPolicy.USE_PROVIDER_ADJUSTED] and actions_applied > 0:
            final_adjusted = True

        out_mdf = MarketDataFrame(
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            source=market_data.source,
            data=df_adj,
            fetched_at=market_data.fetched_at,
            adjusted=final_adjusted,
            quality_report=market_data.quality_report,
            metadata=new_metadata
        )

        return AdjustedMarketData(
            market_data=out_mdf,
            report=report
        )
