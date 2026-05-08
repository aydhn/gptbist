from typing import List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.models import (
    SymbolScanResult, ScanRequest, ScanCandidateStatus
)
from bist_signal_bot.risk.models import RiskDecisionStatus

class ScanFilterEngine:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def filter_symbol_result(self, result: SymbolScanResult, request: ScanRequest) -> SymbolScanResult:
        if result.status == ScanCandidateStatus.ERROR:
            return result

        if not result.signal:
            result.status = ScanCandidateStatus.FILTERED
            result.reasons.append("No signal generated")
            return result

        sig = result.signal
        if sig.score < request.min_signal_score:
            result.status = ScanCandidateStatus.FILTERED
            result.reasons.append(f"Signal score {sig.score} < min {request.min_signal_score}")
            return result

        if sig.confidence < request.min_confidence:
            result.status = ScanCandidateStatus.FILTERED
            result.reasons.append(f"Confidence {sig.confidence} < min {request.min_confidence}")
            return result

        if sig.direction.value in ["WATCH", "FLAT", "AVOID"]:
            result.status = ScanCandidateStatus.WATCH_ONLY
            result.reasons.append(f"Direction is {sig.direction.value}")
            # might return here or continue

        risk = result.risk_decision
        if risk:
            if risk.status == RiskDecisionStatus.REJECTED:
                result.status = ScanCandidateStatus.REJECTED
                result.reasons.append(f"Risk engine rejected: {risk.rejection_reason if getattr(risk, 'rejection_reason', None) else 'Unknown'}")
                return result

            if risk.final_score is not None and risk.final_score < request.min_final_score:
                result.status = ScanCandidateStatus.FILTERED
                result.reasons.append(f"Final score {risk.final_score} < min {request.min_final_score}")
                return result

        # primitive forbidden claim guard
        forbidden = ["kesin al", "kesin sat", "garanti", "risksiz"]
        sig_meta_str = str(sig.metadata).lower()
        if any(f in sig_meta_str for f in forbidden):
            result.status = ScanCandidateStatus.REJECTED
            result.reasons.append("Forbidden claim detected in signal metadata")
            return result

        if result.status not in [ScanCandidateStatus.WATCH_ONLY, ScanCandidateStatus.REJECTED, ScanCandidateStatus.ERROR]:
             result.status = ScanCandidateStatus.PASSED

        return result

    def filter_results(self, results: List[SymbolScanResult], request: ScanRequest) -> List[SymbolScanResult]:
        return [self.filter_symbol_result(r, request) for r in results]

    def should_include_in_top(self, result: SymbolScanResult) -> bool:
        if result.status == ScanCandidateStatus.PASSED:
            return True
        if result.status == ScanCandidateStatus.WATCH_ONLY and self.settings.SCANNER_INCLUDE_WATCH_ONLY:
            return True
        return False
