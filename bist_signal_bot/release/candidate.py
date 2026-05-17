import logging
from datetime import datetime
from typing import Any
import uuid

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.release.models import (
    ReleaseCandidateManifest, ReleaseStage, ReleaseReadinessReport, ReleaseStatus, ReleaseBlocker
)
from bist_signal_bot.release.readiness import ReleaseReadinessEvaluator
from bist_signal_bot.release.rehearsal import SafeLaunchRehearsalRunner
from bist_signal_bot.core.exceptions import ReleaseCandidateError
from bist_signal_bot.core.audit import AuditLogger, AuditEventType

class ReleaseCandidateBuilder:
    def __init__(self,
                 readiness_evaluator: ReleaseReadinessEvaluator | None = None,
                 rehearsal_runner: SafeLaunchRehearsalRunner | None = None,
                 package_builder: Any | None = None,
                 notes_builder: Any | None = None,
                 storage: Any | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)
        self.readiness_evaluator = readiness_evaluator or ReleaseReadinessEvaluator(settings=self.settings, logger=self.logger)
        self.rehearsal_runner = rehearsal_runner
        self.package_builder = package_builder
        self.notes_builder = notes_builder
        self.storage = storage
        self.audit = AuditLogger(self.settings)

    def build_candidate(self,
                        version: str | None = None,
                        stage: ReleaseStage = ReleaseStage.RELEASE_CANDIDATE,
                        run_rehearsal: bool = True,
                        run_package: bool = True,
                        confirm: bool = False) -> ReleaseCandidateManifest:

        ver = version or getattr(self.settings, "RELEASE_VERSION", "0.1.0")
        candidate_id = str(uuid.uuid4())

        self.audit.log_event(AuditEventType.RELEASE_CANDIDATE_STARTED)

        try:
            # 1. Run Readiness Evaluation
            readiness_report = self.readiness_evaluator.evaluate()

            if readiness_report.status not in [ReleaseStatus.READY, ReleaseStatus.PARTIAL_READY]:
                err = f"Cannot build candidate. Readiness is {readiness_report.status.value}"
                self.audit.log_event(AuditEventType.RELEASE_CANDIDATE_FAILED)
                # For testing and MVP, we might still return a failed manifest instead of raising, or raise
                raise ReleaseCandidateError(err)

            # 2. Run Rehearsal if requested
            if run_rehearsal and self.rehearsal_runner:
                rehearsal_result = self.rehearsal_runner.run_rehearsal()
                if rehearsal_result.status == ReleaseStatus.FAILED:
                     self.logger.warning("Rehearsal failed, but continuing candidate build.")

            # 3. Build Notes (Simulated if builder not present)
            notes_path = None
            if self.notes_builder and self.storage:
                notes = self.notes_builder.build_notes(ver, stage, readiness_report)
                notes_path = str(self.storage.save_release_notes(notes))

            # 4. Generate Manifest
            manifest = ReleaseCandidateManifest(
                candidate_id=candidate_id,
                version=ver,
                stage=stage,
                readiness_report_id=readiness_report.readiness_id,
                release_notes_path=notes_path,
                no_real_order_sent=True
            )

            # If storage is available and confirmed, save manifest
            if self.storage and confirm:
                self.storage.save_candidate_manifest(manifest)

            self.audit.log_event(AuditEventType.RELEASE_CANDIDATE_CREATED)
            return manifest

        except Exception as e:
            self.logger.exception("Failed to build release candidate")
            self.audit.log_event(AuditEventType.RELEASE_CANDIDATE_FAILED)
            raise

    def validate_candidate(self, manifest: ReleaseCandidateManifest) -> list[ReleaseBlocker]:
        blockers = []
        if not manifest.no_real_order_sent:
            b = ReleaseBlocker(
                blocker_id="rc_real_order",
                category="SAFETY", # type: ignore
                severity="CRITICAL", # type: ignore
                title="Real Order Flag Detected",
                message="Candidate claims it might send real orders.",
                blocking=True
            )
            blockers.append(b)
        return blockers

    def candidate_summary(self, manifest: ReleaseCandidateManifest) -> dict[str, Any]:
        return {
            "candidate_id": manifest.candidate_id,
            "version": manifest.version,
            "stage": manifest.stage.value,
            "created_at": manifest.created_at.isoformat(),
            "no_real_order_sent": manifest.no_real_order_sent
        }
