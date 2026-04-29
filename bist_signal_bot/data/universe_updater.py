import logging
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditLogger, AuditEventType
from bist_signal_bot.data.models import (
    SymbolGroup,
    SymbolInfo,
    UniverseFileFormat,
    UniverseUpdateAction,
    UniverseUpdateResult,
    UniverseValidationIssue,
    UniverseValidationIssueType,
    UniverseValidationReport,
)
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.data.universe_store import UniverseStore

class UniverseUpdater:
    def __init__(
        self,
        store: UniverseStore,
        settings: Settings,
        audit_logger: AuditLogger | None = None,
        notifier=None,
        logger: logging.Logger | None = None
    ):
        self.store = store
        self.settings = settings
        self.audit_logger = audit_logger
        self.notifier = notifier
        self.logger = logger or logging.getLogger("bist_signal_bot.universe_updater")

    def _log_audit(self, event_type: AuditEventType, message: str, action: str, symbols: list[str], path: str | None = None, passed: bool | None = None, issues: int | None = None):
        if self.audit_logger:
            self.audit_logger.log_universe_update(
                event_type=event_type,
                message=message,
                action=action,
                symbols_affected=symbols,
                file_path=path,
                validation_passed=passed,
                issue_count=issues
            )

    def validate_universe(self, universe: SymbolUniverse) -> UniverseValidationReport:
        issues = []
        all_symbols = universe.list_symbols(active_only=False)

        if not all_symbols:
            issues.append(UniverseValidationIssue(
                issue_type=UniverseValidationIssueType.EMPTY_UNIVERSE,
                severity="ERROR",
                message="Universe contains no symbols."
            ))

        seen_symbols = set()

        active_count = 0
        inactive_count = 0
        duplicate_count = 0
        invalid_count = 0

        for symbol in all_symbols:
            try:
                norm = ensure_valid_internal_symbol(symbol)
                if norm != symbol:
                    issues.append(UniverseValidationIssue(
                        issue_type=UniverseValidationIssueType.INVALID_SYMBOL,
                        severity="WARNING",
                        symbol=symbol,
                        message=f"Symbol '{symbol}' not normalized (expected '{norm}')."
                    ))
            except Exception:
                invalid_count += 1
                issues.append(UniverseValidationIssue(
                    issue_type=UniverseValidationIssueType.INVALID_SYMBOL,
                    severity="ERROR",
                    symbol=symbol,
                    message=f"Symbol '{symbol}' is completely invalid."
                ))
                continue

            if norm in seen_symbols:
                duplicate_count += 1
                issues.append(UniverseValidationIssue(
                    issue_type=UniverseValidationIssueType.DUPLICATE_SYMBOL,
                    severity="ERROR",
                    symbol=symbol,
                    message=f"Duplicate symbol '{symbol}' detected."
                ))
            else:
                seen_symbols.add(norm)

            info = universe.require(symbol)
            if info.is_active:
                active_count += 1
            else:
                inactive_count += 1

        passed = len([i for i in issues if i.severity == "ERROR"]) == 0

        report = UniverseValidationReport(
            total_symbols=len(all_symbols),
            active_symbols=active_count,
            inactive_symbols=inactive_count,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            issues=issues,
            passed=passed
        )
        return report

    def _prepare_update(self) -> SymbolUniverse:
        if self.settings.AUTO_SNAPSHOT_UNIVERSE and self.store.exists():
            self.store.create_snapshot()
        return self.store.load_universe()

    def add_symbol(self, symbol: str, name: str | None = None, groups: list[str] | None = None, notes: str | None = None, save: bool = True) -> UniverseUpdateResult:
        try:
            norm = ensure_valid_internal_symbol(symbol)
            universe = self._prepare_update()

            if universe.contains(norm):
                return UniverseUpdateResult(
                    action=UniverseUpdateAction.ADD,
                    success=False,
                    message=f"Symbol '{norm}' already exists.",
                    error="DuplicateSymbol"
                )

            g_set = set()
            if groups:
                for g in groups:
                    g_set.add(SymbolGroup(g))

            info = SymbolInfo(
                symbol=norm,
                name=name,
                groups=g_set,
                notes=notes,
                is_active=True
            )

            universe.add_symbol(info)
            path = None
            if save:
                path = self.store.save_universe(universe)

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.ADD,
                success=True,
                symbols_affected=[norm],
                message=f"Symbol '{norm}' added successfully.",
                file_path=str(path) if path else None
            )
            self._log_audit(AuditEventType.UNIVERSE_ADD_SYMBOL, res.message, res.action.value, [norm], res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.ADD,
                success=False,
                message=f"Failed to add symbol '{symbol}'.",
                error=str(e)
            )

    def remove_symbol(self, symbol: str, save: bool = True) -> UniverseUpdateResult:
        try:
            norm = ensure_valid_internal_symbol(symbol)
            universe = self._prepare_update()

            if not universe.contains(norm):
                 return UniverseUpdateResult(
                    action=UniverseUpdateAction.REMOVE,
                    success=False,
                    message=f"Symbol '{norm}' not found.",
                    error="NotFound"
                )

            universe.remove_symbol(norm)
            path = None
            if save:
                path = self.store.save_universe(universe)

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.REMOVE,
                success=True,
                symbols_affected=[norm],
                message=f"Symbol '{norm}' removed successfully.",
                file_path=str(path) if path else None
            )
            self._log_audit(AuditEventType.UNIVERSE_REMOVE_SYMBOL, res.message, res.action.value, [norm], res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.REMOVE,
                success=False,
                message=f"Failed to remove symbol '{symbol}'.",
                error=str(e)
            )

    def deactivate_symbol(self, symbol: str, save: bool = True) -> UniverseUpdateResult:
        try:
            norm = ensure_valid_internal_symbol(symbol)
            universe = self._prepare_update()

            if not universe.contains(norm):
                 return UniverseUpdateResult(
                    action=UniverseUpdateAction.DEACTIVATE,
                    success=False,
                    message=f"Symbol '{norm}' not found.",
                    error="NotFound"
                )

            universe.deactivate_symbol(norm)
            path = None
            if save:
                path = self.store.save_universe(universe)

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.DEACTIVATE,
                success=True,
                symbols_affected=[norm],
                message=f"Symbol '{norm}' deactivated.",
                file_path=str(path) if path else None
            )
            self._log_audit(AuditEventType.UNIVERSE_DEACTIVATE_SYMBOL, res.message, res.action.value, [norm], res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.DEACTIVATE,
                success=False,
                message=f"Failed to deactivate symbol '{symbol}'.",
                error=str(e)
            )

    def activate_symbol(self, symbol: str, save: bool = True) -> UniverseUpdateResult:
        try:
            norm = ensure_valid_internal_symbol(symbol)
            universe = self._prepare_update()

            if not universe.contains(norm):
                 return UniverseUpdateResult(
                    action=UniverseUpdateAction.ACTIVATE,
                    success=False,
                    message=f"Symbol '{norm}' not found.",
                    error="NotFound"
                )

            universe.activate_symbol(norm)
            path = None
            if save:
                path = self.store.save_universe(universe)

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.ACTIVATE,
                success=True,
                symbols_affected=[norm],
                message=f"Symbol '{norm}' activated.",
                file_path=str(path) if path else None
            )
            self._log_audit(AuditEventType.UNIVERSE_ACTIVATE_SYMBOL, res.message, res.action.value, [norm], res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.ACTIVATE,
                success=False,
                message=f"Failed to activate symbol '{symbol}'.",
                error=str(e)
            )

    def import_from_file(self, path: Path, merge: bool = True, deactivate_missing: bool = False) -> UniverseUpdateResult:
        if self.settings.AUTO_SNAPSHOT_UNIVERSE and self.store.exists():
            self.store.create_snapshot()

        res = self.store.import_universe(path, merge=merge, deactivate_missing=deactivate_missing)

        if res.success:
            universe = self.store.load_universe()
            res.validation_report = self.validate_universe(universe)

        self._log_audit(
            AuditEventType.UNIVERSE_IMPORT,
            res.message,
            res.action.value,
            res.symbols_affected,
            res.file_path,
            res.validation_report.passed if res.validation_report else None,
            len(res.validation_report.issues) if res.validation_report else None
        )
        self.send_update_summary(res)
        return res

    def export_to_file(self, format: UniverseFileFormat, output_path: Path | None = None) -> UniverseUpdateResult:
        try:
            path = self.store.export_universe(format, output_path)
            res = UniverseUpdateResult(
                action=UniverseUpdateAction.EXPORT,
                success=True,
                message=f"Universe exported to {path}",
                file_path=str(path)
            )
            self._log_audit(AuditEventType.UNIVERSE_EXPORT, res.message, res.action.value, [], res.file_path)
            return res
        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.EXPORT,
                success=False,
                message="Failed to export universe.",
                error=str(e)
            )

    def create_snapshot(self) -> UniverseUpdateResult:
        try:
            path = self.store.create_snapshot()
            res = UniverseUpdateResult(
                action=UniverseUpdateAction.SNAPSHOT,
                success=True,
                message=f"Snapshot created at {path}",
                snapshot_path=str(path)
            )
            self._log_audit(AuditEventType.UNIVERSE_SNAPSHOT, res.message, res.action.value, [], res.snapshot_path)
            return res
        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.SNAPSHOT,
                success=False,
                message="Failed to create snapshot.",
                error=str(e)
            )

    def add_to_watchlist(self, watchlist_name: str, symbols: list[str]) -> UniverseUpdateResult:
        try:
            current = self.store.load_watchlist(watchlist_name)

            universe = self.store.load_universe()
            to_add = []
            issues = []

            for s in symbols:
                norm = ensure_valid_internal_symbol(s)
                if not universe.contains(norm):
                    issues.append(UniverseValidationIssue(
                        issue_type=UniverseValidationIssueType.INVALID_SYMBOL,
                        severity="WARNING",
                        symbol=norm,
                        message=f"Symbol '{norm}' not in universe."
                    ))
                if norm not in current:
                    current.append(norm)
                    to_add.append(norm)

            path = self.store.save_watchlist(watchlist_name, current)

            report = UniverseValidationReport(
                total_symbols=len(current),
                active_symbols=0,
                inactive_symbols=0,
                duplicate_count=0,
                invalid_count=0,
                issues=issues,
                passed=len(issues) == 0
            )

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.WATCHLIST_ADD,
                success=True,
                symbols_affected=to_add,
                message=f"Added {len(to_add)} symbols to watchlist '{watchlist_name}'.",
                file_path=str(path),
                validation_report=report
            )
            self._log_audit(AuditEventType.WATCHLIST_UPDATE, res.message, res.action.value, to_add, res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.WATCHLIST_ADD,
                success=False,
                message=f"Failed to add to watchlist '{watchlist_name}'.",
                error=str(e)
            )

    def remove_from_watchlist(self, watchlist_name: str, symbols: list[str]) -> UniverseUpdateResult:
        try:
            current = self.store.load_watchlist(watchlist_name)

            to_remove = []
            for s in symbols:
                norm = ensure_valid_internal_symbol(s)
                if norm in current:
                    current.remove(norm)
                    to_remove.append(norm)

            path = self.store.save_watchlist(watchlist_name, current)

            res = UniverseUpdateResult(
                action=UniverseUpdateAction.WATCHLIST_REMOVE,
                success=True,
                symbols_affected=to_remove,
                message=f"Removed {len(to_remove)} symbols from watchlist '{watchlist_name}'.",
                file_path=str(path)
            )
            self._log_audit(AuditEventType.WATCHLIST_UPDATE, res.message, res.action.value, to_remove, res.file_path)
            return res

        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.WATCHLIST_REMOVE,
                success=False,
                message=f"Failed to remove from watchlist '{watchlist_name}'.",
                error=str(e)
            )

    def send_update_summary(self, result: UniverseUpdateResult) -> None:
        if not self.settings.UNIVERSE_SEND_TELEGRAM_SUMMARY:
            return

        if self.notifier:
            try:
                from bist_signal_bot.notifications.formatter import format_universe_update
                msg = format_universe_update(result)
                self.notifier.send_text(title="Universe Update Summary", body=msg)
            except Exception as e:
                self.logger.error(f"Failed to send universe update summary to Telegram: {e}")
