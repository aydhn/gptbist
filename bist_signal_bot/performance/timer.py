import time
import uuid
import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from bist_signal_bot.performance.models import ProfileSpan, ProfileResult, BenchmarkType

class PerformanceTimer:
    def __init__(self):
        self._spans: Dict[str, ProfileSpan] = {}
        self._active_spans: List[str] = []

    def start_span(self, name: str, module: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ProfileSpan:
        span_id = str(uuid.uuid4())
        span = ProfileSpan(
            span_id=span_id,
            name=name,
            module=module,
            started_at=datetime.datetime.now(datetime.timezone.utc),
            metadata=metadata or {}
        )

        # Store start times using monotonic clock for accurate elapsed calculation
        span.metadata['_start_monotonic'] = time.monotonic()

        # Link to parent if nested
        if self._active_spans:
            parent_id = self._active_spans[-1]
            if parent_id in self._spans:
                self._spans[parent_id].children.append(span_id)

        self._spans[span_id] = span
        self._active_spans.append(span_id)
        return span

    def finish_span(self, span_id: str) -> ProfileSpan:
        if span_id not in self._spans:
            raise ValueError(f"Span {span_id} not found")

        span = self._spans[span_id]
        if span.finished_at is not None:
            return span

        end_monotonic = time.monotonic()
        span.finished_at = datetime.datetime.now(datetime.timezone.utc)
        start_monotonic = span.metadata.pop('_start_monotonic', end_monotonic)
        span.elapsed_seconds = max(0.0, end_monotonic - start_monotonic)

        if self._active_spans and self._active_spans[-1] == span_id:
            self._active_spans.pop()
        else:
            # Handle out-of-order closing or exceptions
            if span_id in self._active_spans:
                self._active_spans.remove(span_id)

        return span

    @contextmanager
    def span(self, name: str, module: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        span_obj = self.start_span(name, module, metadata)
        try:
            yield span_obj
        finally:
            self.finish_span(span_obj.span_id)

    def current_spans(self) -> List[ProfileSpan]:
        return list(self._spans.values())

    def build_profile_result(self, benchmark_type: BenchmarkType) -> ProfileResult:
        # Finish any dangling active spans just in case
        for span_id in list(self._active_spans):
            self.finish_span(span_id)

        spans = list(self._spans.values())
        if not spans:
            started_at = datetime.datetime.now(datetime.timezone.utc)
            finished_at = started_at
            elapsed = 0.0
        else:
            started_at = min(s.started_at for s in spans)
            finished_at = max(s.finished_at for s in spans if s.finished_at is not None)
            elapsed = sum(s.elapsed_seconds for s in spans if not any(s.span_id in parent.children for parent in spans))

        return ProfileResult(
            profile_id=str(uuid.uuid4()),
            benchmark_type=benchmark_type,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            spans=spans
        )
