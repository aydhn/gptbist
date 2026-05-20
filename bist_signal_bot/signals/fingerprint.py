import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional
from bist_signal_bot.signals.models import SignalFingerprint

class SignalFingerprintBuilder:
    def build_from_signal(self, signal: Any, source_type: str, timeframe: Optional[str] = None) -> SignalFingerprint:
        # Determine properties dynamically to support diverse signal objects
        symbol = getattr(signal, 'symbol', 'UNKNOWN')
        strategy_name = getattr(signal, 'strategy_name', None)
        direction = getattr(signal, 'direction', None)

        # Round the score to avoid small deviations triggering new fingerprints
        score = getattr(signal, 'score', None)
        rounded_score = round(score, 1) if isinstance(score, (int, float)) else None

        payload = {
            "symbol": symbol,
            "strategy_name": strategy_name,
            "direction": direction,
            "source_type": source_type,
            "timeframe": timeframe,
            "rounded_score_bucket": rounded_score,
            "major_reasons": getattr(signal, 'reasons', [])[:3]  # taking up to 3 major reasons
        }

        # Handle consensus decision if present
        consensus_decision = getattr(signal, 'decision', None)
        if consensus_decision:
            payload["consensus_decision"] = consensus_decision

        normalized = self.normalize_payload(payload)
        fingerprint_id = self.hash_payload(normalized)

        return SignalFingerprint(
            fingerprint_id=fingerprint_id,
            symbol=symbol,
            strategy_name=strategy_name,
            signal_direction=direction,
            source_type=source_type,
            timeframe=timeframe,
            normalized_payload_hash=fingerprint_id,
            created_at=datetime.utcnow(),
            metadata={"normalized_payload": normalized}
        )

    def normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Sort lists, format floats, lowercase strings for consistent hashing
        normalized = {}
        for k, v in sorted(payload.items()):
            if isinstance(v, float):
                normalized[k] = round(v, 2)
            elif isinstance(v, str):
                normalized[k] = v.lower()
            elif isinstance(v, list):
                normalized[k] = sorted([str(x).lower() for x in v])
            else:
                normalized[k] = v
        return normalized

    def hash_payload(self, payload: Dict[str, Any]) -> str:
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    def is_same_family(self, left: SignalFingerprint, right: SignalFingerprint) -> bool:
        if left.symbol != right.symbol:
            return False
        if left.strategy_name != right.strategy_name:
            return False
        if left.signal_direction != right.signal_direction:
            return False
        if left.source_type != right.source_type:
            return False
        return True
