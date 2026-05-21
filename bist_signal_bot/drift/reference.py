import json
import logging
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_drift_dir
from bist_signal_bot.drift.models import DriftReferenceWindow, DriftDomain, ReferenceWindowType
from bist_signal_bot.core.exceptions import DriftReferenceError

logger = logging.getLogger(__name__)

class DriftReferenceManager:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_drift_dir(self.settings)

    def build_reference_from_feature_store(self, domain: DriftDomain, feature_names: list[str] | None = None, days: int = 90) -> DriftReferenceWindow:
        return DriftReferenceWindow(
            reference_id=str(uuid.uuid4()),
            window_type=ReferenceWindowType.LAST_N_DAYS,
            domain=domain,
            sample_count=0,
            feature_names=feature_names or [],
            metadata={"days": days, "source": "feature_store"}
        )

    def build_reference_from_research_ledger(self, domain: DriftDomain, days: int = 90) -> DriftReferenceWindow:
        return DriftReferenceWindow(
            reference_id=str(uuid.uuid4()),
            window_type=ReferenceWindowType.LAST_N_DAYS,
            domain=domain,
            sample_count=0,
            metadata={"days": days, "source": "research_ledger"}
        )

    def build_reference_from_model_training(self, model_id: str) -> DriftReferenceWindow:
        return DriftReferenceWindow(
            reference_id=str(uuid.uuid4()),
            window_type=ReferenceWindowType.MODEL_TRAINING_WINDOW,
            domain=DriftDomain.MODEL_SCORE,
            sample_count=0,
            metadata={"model_id": model_id, "source": "model_registry"}
        )

    def save_reference(self, window: DriftReferenceWindow, data: pd.DataFrame | None = None, confirm: bool = False) -> Path:
        if self.settings.DRIFT_REFERENCE_UPDATE_REQUIRES_CONFIRM and not confirm:
            raise DriftReferenceError("Updating a drift reference window requires explicit confirmation (confirm=True)")

        try:
            ref_dir = self.base_dir / "references" / window.reference_id
            ref_dir.mkdir(parents=True, exist_ok=True)

            meta_path = ref_dir / "reference_window.json"
            with open(meta_path, "w") as f:
                json.dump(window.model_dump(mode='json'), f, indent=2)

            if data is not None and not data.empty:
                 if window.domain == DriftDomain.FEATURE:
                      data_path = ref_dir / "reference_features.parquet"
                      data.to_parquet(data_path)
                      window.source_path = str(data_path)
                 elif window.domain in [DriftDomain.MODEL_SCORE, DriftDomain.MODEL_CALIBRATION]:
                      data_path = ref_dir / "reference_predictions.csv"
                      data.to_csv(data_path, index=False)
                      window.source_path = str(data_path)

                 with open(meta_path, "w") as f:
                      json.dump(window.model_dump(mode='json'), f, indent=2)

            return ref_dir
        except Exception as e:
            logger.error(f"Failed to save drift reference: {e}")
            raise DriftReferenceError(f"Failed to save reference: {e}")

    def load_reference(self, reference_id: str | None = None, domain: DriftDomain | None = None) -> tuple[DriftReferenceWindow | None, pd.DataFrame | None]:
        ref_dir = self.base_dir / "references"
        if not ref_dir.exists():
            return None, None

        try:
            if reference_id:
                target_dir = ref_dir / reference_id
                if not target_dir.exists():
                    return None, None
                meta_path = target_dir / "reference_window.json"
                if not meta_path.exists():
                    return None, None
                with open(meta_path, "r") as f:
                    data = json.load(f)
                window = DriftReferenceWindow(**data)

                df = None
                if window.source_path:
                    p = Path(window.source_path)
                    if p.exists():
                        if p.suffix == ".parquet":
                            df = pd.read_parquet(p)
                        elif p.suffix == ".csv":
                            df = pd.read_csv(p)
                return window, df
            elif domain:
                refs = self.list_references()
                domain_refs = [r for r in refs if r.get("domain") == domain.value]
                if domain_refs:
                     latest_id = domain_refs[0]["reference_id"]
                     return self.load_reference(reference_id=latest_id)
            return None, None
        except Exception as e:
            logger.error(f"Failed to load drift reference: {e}")
            raise DriftReferenceError(f"Failed to load reference: {e}")

    def list_references(self, limit: int = 20) -> list[dict[str, Any]]:
        ref_dir = self.base_dir / "references"
        if not ref_dir.exists():
            return []

        all_refs = []
        for d in ref_dir.iterdir():
            if d.is_dir():
                meta_path = d / "reference_window.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r") as f:
                            data = json.load(f)
                            all_refs.append(data)
                    except Exception:
                        pass

        all_refs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return all_refs[:limit]
