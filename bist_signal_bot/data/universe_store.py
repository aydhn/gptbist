import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import UniverseStoreError
from bist_signal_bot.data.models import (
    AssetType,
    Market,
    SymbolGroup,
    SymbolInfo,
)
from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS, SymbolUniverse
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.storage.paths import (
    get_universe_dir,
    get_universe_file_path,
    get_universe_snapshots_dir,
    get_watchlists_dir,
)

SCHEMA_VERSION = "1.0"

class UniverseStore:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def get_universe_dir(self) -> Path:
        if self.base_dir:
            path = self.base_dir / self.settings.UNIVERSE_DIR_NAME
            path.mkdir(parents=True, exist_ok=True)
            return path
        return get_universe_dir(self.settings)

    def get_universe_file_path(self) -> Path:
        if self.base_dir:
            return self.get_universe_dir() / self.settings.UNIVERSE_FILE_NAME
        return get_universe_file_path(self.settings)

    def get_watchlists_dir(self) -> Path:
        if self.base_dir:
            path = self.get_universe_dir() / self.settings.WATCHLISTS_DIR_NAME
            path.mkdir(parents=True, exist_ok=True)
            return path
        return get_watchlists_dir(self.settings)

    def get_snapshots_dir(self) -> Path:
        if self.base_dir:
            path = self.get_universe_dir() / self.settings.UNIVERSE_SNAPSHOTS_DIR_NAME
            path.mkdir(parents=True, exist_ok=True)
            return path
        return get_universe_snapshots_dir(self.settings)

    def exists(self) -> bool:
        return self.get_universe_file_path().exists()

    def load_universe(self) -> SymbolUniverse:
        path = self.get_universe_file_path()
        if not path.exists():
            return SymbolUniverse()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise UniverseStoreError(f"Corrupt universe file ({path}): Invalid JSON - {e}")
        except Exception as e:
            raise UniverseStoreError(f"Failed to load universe file: {e}")

        if "schema_version" not in data:
            raise UniverseStoreError(f"Corrupt universe file ({path}): Missing schema_version")

        symbols_data = data.get("symbols", [])
        universe = SymbolUniverse()

        for item in symbols_data:
            try:
                symbol = ensure_valid_internal_symbol(item.get("symbol", ""))
                groups = {SymbolGroup(g) for g in item.get("groups", [])}
                market = Market(item.get("market", Market.BIST.value))
                asset_type = AssetType(item.get("asset_type", AssetType.EQUITY.value))

                info = SymbolInfo(
                    symbol=symbol,
                    name=item.get("name"),
                    market=market,
                    asset_type=asset_type,
                    currency=item.get("currency", "TRY"),
                    groups=groups,
                    is_active=item.get("is_active", True),
                    notes=item.get("notes")
                )
                if not universe.contains(symbol):
                    universe.add_symbol(info)
            except Exception as e:
                raise UniverseStoreError(f"Error parsing symbol data for {item.get('symbol')}: {e}")

        return universe

    def save_universe(self, universe: SymbolUniverse) -> Path:
        path = self.get_universe_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        symbols_list = []
        for symbol in universe.list_symbols(active_only=False):
            info = universe.require(symbol)
            symbols_list.append({
                "symbol": info.symbol,
                "name": info.name,
                "market": info.market.value,
                "asset_type": info.asset_type.value,
                "currency": info.currency,
                "groups": [g.value for g in info.groups],
                "is_active": info.is_active,
                "notes": info.notes
            })

        data = {
            "schema_version": SCHEMA_VERSION,
            "name": "BIST Local Universe",
            "description": "Local manually managed BIST symbol universe",
            "updated_at": datetime.now(UTC).isoformat(),
            "symbols": symbols_list
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise UniverseStoreError(f"Failed to save universe to {path}: {e}")

        return path

    def initialize_default_universe(self, overwrite: bool = False) -> 'UniverseUpdateResult':
        from bist_signal_bot.data.models import UniverseUpdateAction, UniverseUpdateResult

        path = self.get_universe_file_path()
        if path.exists() and not overwrite:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.VALIDATE,
                success=True,
                message="Universe already exists, skipped initialization.",
                file_path=str(path)
            )

        universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
        try:
            saved_path = self.save_universe(universe)
            return UniverseUpdateResult(
                action=UniverseUpdateAction.VALIDATE,
                success=True,
                message="Default seed universe initialized.",
                symbols_affected=universe.list_symbols(active_only=False),
                file_path=str(saved_path)
            )
        except Exception as e:
            return UniverseUpdateResult(
                action=UniverseUpdateAction.VALIDATE,
                success=False,
                message="Failed to initialize universe.",
                error=str(e)
            )

    def export_universe(self, format: 'UniverseFileFormat', output_path: Path | None = None) -> Path:
        from bist_signal_bot.data.models import UniverseFileFormat
        universe = self.load_universe()

        if not output_path:
            ext = ".json" if format == UniverseFileFormat.JSON else ".csv"
            output_path = self.get_universe_dir() / f"export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}{ext}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == UniverseFileFormat.JSON:
            original_file = self.get_universe_file_path()
            if original_file.exists() and output_path != original_file:
                 import shutil
                 shutil.copy2(original_file, output_path)
            else:
                 self.save_universe(universe)
                 symbols_list = []
                 for symbol in universe.list_symbols(active_only=False):
                     info = universe.require(symbol)
                     symbols_list.append({
                         "symbol": info.symbol,
                         "name": info.name,
                         "market": info.market.value,
                         "asset_type": info.asset_type.value,
                         "currency": info.currency,
                         "groups": [g.value for g in info.groups],
                         "is_active": info.is_active,
                         "notes": info.notes
                     })
                 data = {
                     "schema_version": SCHEMA_VERSION,
                     "name": "BIST Local Universe Export",
                     "description": "Exported symbol universe",
                     "updated_at": datetime.now(UTC).isoformat(),
                     "symbols": symbols_list
                 }
                 with open(output_path, "w", encoding="utf-8") as f:
                     json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["symbol", "name", "groups", "is_active", "notes", "market", "asset_type", "currency"])
                for symbol in universe.list_symbols(active_only=False):
                    info = universe.require(symbol)
                    writer.writerow([
                        info.symbol,
                        info.name or "",
                        "|".join([g.value for g in info.groups]),
                        str(info.is_active).lower(),
                        info.notes or "",
                        info.market.value,
                        info.asset_type.value,
                        info.currency
                    ])

        return output_path

    def _parse_json_universe(self, path: Path) -> list['SymbolInfo']:
        imported_symbols = []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        symbols_data = data.get("symbols", [])
        for item in symbols_data:
            sym = item.get("symbol")
            if not sym: continue
            sym = ensure_valid_internal_symbol(sym)
            groups = {SymbolGroup(g) for g in item.get("groups", [])}
            info = SymbolInfo(
                symbol=sym,
                name=item.get("name"),
                market=Market(item.get("market", Market.BIST.value)),
                asset_type=AssetType(item.get("asset_type", AssetType.EQUITY.value)),
                currency=item.get("currency", "TRY"),
                groups=groups,
                is_active=item.get("is_active", True),
                notes=item.get("notes")
            )
            imported_symbols.append(info)
        return imported_symbols

    def _parse_csv_universe(self, path: Path) -> list['SymbolInfo']:
        imported_symbols = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = row.get("symbol", "").strip()
                if not sym: continue
                sym = ensure_valid_internal_symbol(sym)

                g_str = row.get("groups", "")
                groups = set()
                if g_str:
                    delim = "|" if "|" in g_str else ","
                    for g in g_str.split(delim):
                        g = g.strip()
                        if g:
                            try:
                                groups.add(SymbolGroup(g))
                            except ValueError:
                                pass

                is_active_str = row.get("is_active", "true").lower()
                is_active = is_active_str in ("true", "1", "yes", "")

                info = SymbolInfo(
                    symbol=sym,
                    name=row.get("name", "").strip() or None,
                    market=Market(row.get("market", Market.BIST.value).strip() or Market.BIST.value),
                    asset_type=AssetType(row.get("asset_type", AssetType.EQUITY.value).strip() or AssetType.EQUITY.value),
                    currency=row.get("currency", "TRY").strip() or "TRY",
                    groups=groups,
                    is_active=is_active,
                    notes=row.get("notes", "").strip() or None
                )
                imported_symbols.append(info)
        return imported_symbols

    def import_universe(self, path: Path, merge: bool = True, deactivate_missing: bool = False) -> 'UniverseUpdateResult':
        from bist_signal_bot.data.models import UniverseUpdateAction, UniverseUpdateResult

        if not path.exists():
            return UniverseUpdateResult(
                action=UniverseUpdateAction.IMPORT,
                success=False,
                message=f"Import file not found: {path}",
                error="File not found"
            )

        current_universe = self.load_universe()
        if not merge:
            current_universe = SymbolUniverse()

        try:
            if path.suffix.lower() == ".json":
                imported_symbols = self._parse_json_universe(path)
            else:
                imported_symbols = self._parse_csv_universe(path)

            affected = []
            imported_symbol_names = {info.symbol for info in imported_symbols}

            for info in imported_symbols:
                if current_universe.contains(info.symbol):
                    current_universe.remove_symbol(info.symbol)
                current_universe.add_symbol(info)
                affected.append(info.symbol)

            if deactivate_missing and merge:
                for existing in current_universe.list_symbols(active_only=True):
                    if existing not in imported_symbol_names:
                        current_universe.deactivate_symbol(existing)
                        affected.append(existing)

            self.save_universe(current_universe)

            return UniverseUpdateResult(
                action=UniverseUpdateAction.IMPORT,
                success=True,
                message=f"Successfully imported {len(imported_symbols)} symbols.",
                symbols_affected=affected,
                file_path=str(path)
            )

        except Exception as e:
            from bist_signal_bot.core.exceptions import UniverseImportError
            return UniverseUpdateResult(
                action=UniverseUpdateAction.IMPORT,
                success=False,
                message="Failed to import universe.",
                error=str(e),
                file_path=str(path)
            )


    def create_snapshot(self, universe: SymbolUniverse | None = None) -> Path:
        if not universe:
            universe = self.load_universe()

        timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
        snapshot_name = f"{Path(self.settings.UNIVERSE_FILE_NAME).stem}_{timestamp}.json"
        snapshot_path = self.get_snapshots_dir() / snapshot_name

        symbols_list = []
        for symbol in universe.list_symbols(active_only=False):
            info = universe.require(symbol)
            symbols_list.append({
                "symbol": info.symbol,
                "name": info.name,
                "market": info.market.value,
                "asset_type": info.asset_type.value,
                "currency": info.currency,
                "groups": [g.value for g in info.groups],
                "is_active": info.is_active,
                "notes": info.notes
            })

        data = {
            "schema_version": SCHEMA_VERSION,
            "name": "BIST Local Universe Snapshot",
            "description": f"Snapshot taken at {timestamp}",
            "updated_at": datetime.now(UTC).isoformat(),
            "symbols": symbols_list
        }

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return snapshot_path

    def load_watchlist(self, name: str) -> list[str]:
        path = self.get_watchlists_dir() / f"{name}.json"
        if not path.exists():
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ensure_valid_internal_symbol(s) for s in data.get("symbols", [])]
        except Exception:
            return []

    def save_watchlist(self, name: str, symbols: list[str]) -> Path:
        path = self.get_watchlists_dir() / f"{name}.json"
        normalized_symbols = [ensure_valid_internal_symbol(s) for s in symbols]

        data = {
            "name": name,
            "updated_at": datetime.now(UTC).isoformat(),
            "symbols": normalized_symbols
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path

    def list_watchlists(self) -> list[str]:
        dir_path = self.get_watchlists_dir()
        if not dir_path.exists():
            return []
        return [p.stem for p in dir_path.glob("*.json")]
