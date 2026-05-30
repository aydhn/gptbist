from datetime import datetime
import uuid
from typing import Optional

from bist_signal_bot.docs_hub.models import (
    DocsIndex, DocPage, DocsSearchResult, DocsStatus, DocAudience, DocKind
)

class DocsSearchEngine:
    def __init__(self, settings=None, base_dir=None):
        pass

    def search(self, query: str, index: Optional[DocsIndex] = None, limit: int = 20) -> DocsSearchResult:
        if not index:
            return DocsSearchResult(
                result_id=str(uuid.uuid4()),
                query=query,
                created_at=datetime.utcnow(),
                matches=[],
                status=DocsStatus.FAIL,
                warnings=["No index provided"]
            )

        query_lower = query.lower()
        matches = []
        for page in index.pages:
            score = self.score_page(query_lower, page)
            if score > 0:
                matches.append({"page": page, "score": score})

        matches.sort(key=lambda x: x["score"], reverse=True)
        matches = matches[:limit]

        return DocsSearchResult(
            result_id=str(uuid.uuid4()),
            query=query,
            created_at=datetime.utcnow(),
            matches=[{"page_id": m["page"].page_id, "title": m["page"].title, "score": m["score"]} for m in matches],
            status=DocsStatus.PASS if matches else DocsStatus.MISSING
        )

    def score_page(self, query: str, page: DocPage) -> float:
        score = 0.0
        if query in page.title.lower():
            score += 10.0
        if query in page.summary.lower():
            score += 5.0
        for h in page.headings:
            if query in h.lower():
                score += 2.0
        return score

    def filter_by_audience(self, results: DocsSearchResult, audience: Optional[DocAudience] = None) -> DocsSearchResult:
        # Simplified for mock
        return results

    def filter_by_kind(self, results: DocsSearchResult, kind: Optional[DocKind] = None) -> DocsSearchResult:
        # Simplified for mock
        return results
