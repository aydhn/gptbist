import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import GovernanceStorageError
from bist_signal_bot.governance.models import (
    AuditReviewResult,
    ComplianceAttestation,
    EvidencePackManifest,
    GovernanceGateResult,
    GovernancePolicy,
)

class GovernanceStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        from bist_signal_bot.storage.paths import get_governance_dir
        self.base_dir = base_dir or get_governance_dir(self.settings)

    def save_policy(self, policy: GovernancePolicy) -> Path:
        policy_dir = self.base_dir / "policy"
        policy_dir.mkdir(parents=True, exist_ok=True)
        path = policy_dir / "governance_policy.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(policy.model_dump_json(indent=2))
            return path
        except Exception as e:
            raise GovernanceStorageError(f"Failed to save policy: {e}")

    def load_policy(self) -> GovernancePolicy | None:
        path = self.base_dir / "policy" / "governance_policy.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GovernancePolicy(**data)
        except Exception as e:
            raise GovernanceStorageError(f"Failed to load policy: {e}")

    def save_review(self, result: AuditReviewResult) -> dict[str, Path]:
        date_str = result.generated_at.strftime("%Y%m%d")
        review_dir = self.base_dir / "reviews" / date_str / result.review_id
        review_dir.mkdir(parents=True, exist_ok=True)

        paths = {}
        json_path = review_dir / "audit_review.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
            paths["json"] = json_path
        except Exception as e:
            raise GovernanceStorageError(f"Failed to save audit review: {e}")

        # Also maintain a latest.json
        latest_path = self.base_dir / "reviews" / "latest.json"
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(latest_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
            paths["latest"] = latest_path
        except Exception:
            pass # ignore if latest fails

        return paths

    def load_latest_review(self) -> AuditReviewResult | None:
        latest_path = self.base_dir / "reviews" / "latest.json"
        if not latest_path.exists():
            return None
        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AuditReviewResult(**data)
        except Exception as e:
            raise GovernanceStorageError(f"Failed to load latest review: {e}")

    def save_gate_result(self, result: GovernanceGateResult) -> dict[str, Path]:
        date_str = result.generated_at.strftime("%Y%m%d")
        gate_dir = self.base_dir / "gates" / date_str / result.gate_id
        gate_dir.mkdir(parents=True, exist_ok=True)

        json_path = gate_dir / "gate_result.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
            return {"json": json_path}
        except Exception as e:
            raise GovernanceStorageError(f"Failed to save gate result: {e}")

    def save_evidence_manifest(self, manifest: EvidencePackManifest) -> dict[str, Path]:
        date_str = manifest.created_at.strftime("%Y%m%d")
        manifest_dir = self.base_dir / "evidence" / date_str / manifest.pack_id
        manifest_dir.mkdir(parents=True, exist_ok=True)

        json_path = manifest_dir / "evidence_manifest.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(manifest.model_dump_json(indent=2))
            return {"json": json_path}
        except Exception as e:
            raise GovernanceStorageError(f"Failed to save evidence manifest: {e}")

    def save_attestation(self, attestation: ComplianceAttestation) -> dict[str, Path]:
        date_str = attestation.created_at.strftime("%Y%m%d")
        att_dir = self.base_dir / "attestations" / date_str / attestation.attestation_id
        att_dir.mkdir(parents=True, exist_ok=True)

        json_path = att_dir / "attestation.json"
        md_path = att_dir / "attestation.md"

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(attestation.model_dump_json(indent=2))

            from bist_signal_bot.governance.attestation import ComplianceAttestationBuilder
            builder = ComplianceAttestationBuilder(self.settings)
            md_content = builder.render_markdown(attestation)

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            return {"json": json_path, "md": md_path}
        except Exception as e:
            raise GovernanceStorageError(f"Failed to save attestation: {e}")

    def list_recent_reviews(self, limit: int = 20) -> list[dict[str, Any]]:
        reviews = []
        reviews_dir = self.base_dir / "reviews"
        if not reviews_dir.exists():
            return reviews

        for path in sorted(reviews_dir.glob("*/rev_*/audit_review.json"), reverse=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    reviews.append(data)
                if len(reviews) >= limit:
                    break
            except Exception:
                continue
        return reviews
