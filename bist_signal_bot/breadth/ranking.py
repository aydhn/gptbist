from datetime import datetime
from typing import Any

from bist_signal_bot.breadth.models import CrossSectionalRankItem, RelativeStrengthScore, RankingDirection

class CrossSectionalRanker:
    def __init__(self, settings=None):
        self.settings = settings

        self.w_rs = getattr(settings, "BREADTH_WEIGHT_RELATIVE_STRENGTH", 0.45) if settings else 0.45
        self.w_am = getattr(settings, "BREADTH_WEIGHT_ABSOLUTE_MOMENTUM", 0.20) if settings else 0.20
        self.w_ba = getattr(settings, "BREADTH_WEIGHT_BREADTH_ALIGNMENT", 0.15) if settings else 0.15
        self.w_fu = getattr(settings, "BREADTH_WEIGHT_FUNDAMENTAL", 0.10) if settings else 0.10
        self.w_lq = getattr(settings, "BREADTH_WEIGHT_LIQUIDITY", 0.10) if settings else 0.10

    def rank_symbols(self, relative_scores: list[RelativeStrengthScore], fundamental_scorecards: dict[str, Any] | None = None, liquidity_scores: dict[str, float] | None = None, top_n: int | None = None) -> list[CrossSectionalRankItem]:
        items = []
        fundamentals = fundamental_scorecards or {}
        liquidity = liquidity_scores or {}

        for rs in relative_scores:
            f_score = fundamentals.get(rs.symbol, {}).get("overall_score", 50.0) if fundamentals.get(rs.symbol) else None
            l_score = liquidity.get(rs.symbol, 50.0)

            comp_vals = {
                "relative_strength": rs.composite_score,
                "absolute_momentum": rs.absolute_momentum_score or 50.0,
                "breadth_alignment": 50.0,
                "fundamental_score": f_score,
                "liquidity_score": l_score
            }

            scored_comps = self.score_components(comp_vals)
            comp_score = 0.0
            total_w = 0.0

            if scored_comps["relative_strength"] is not None:
                comp_score += scored_comps["relative_strength"] * self.w_rs
                total_w += self.w_rs
            if scored_comps["absolute_momentum"] is not None:
                comp_score += scored_comps["absolute_momentum"] * self.w_am
                total_w += self.w_am
            if scored_comps["breadth_alignment"] is not None:
                comp_score += scored_comps["breadth_alignment"] * self.w_ba
                total_w += self.w_ba
            if scored_comps["fundamental_score"] is not None:
                comp_score += scored_comps["fundamental_score"] * self.w_fu
                total_w += self.w_fu
            if scored_comps["liquidity_score"] is not None:
                comp_score += scored_comps["liquidity_score"] * self.w_lq
                total_w += self.w_lq

            final_score = (comp_score / total_w) if total_w > 0 else 50.0

            item = CrossSectionalRankItem(
                symbol=rs.symbol,
                as_of_date=rs.as_of_date,
                rank=0,
                percentile=0.0,
                composite_score=final_score,
                components=scored_comps,
                sector=rs.sector
            )
            items.append(item)

        items.sort(key=lambda x: (x.composite_score, x.symbol), reverse=True)

        n = len(items)
        for i, item in enumerate(items):
            item.rank = i + 1
            item.percentile = ((n - i) / n) * 100 if n > 0 else 100.0

        if top_n is not None:
            items = items[:top_n]

        return items

    def score_components(self, comp_vals: dict[str, float | None]) -> dict[str, float | None]:
        # Simple passthrough for now; can normalize to 0-100 here if needed.
        res = {}
        for k, v in comp_vals.items():
            if v is not None:
                res[k] = max(0.0, min(100.0, v))
            else:
                res[k] = None
        return res

    def normalize_component(self, values: dict[str, float], direction: RankingDirection) -> dict[str, float]:
        if not values:
            return values
        v_min = min(values.values())
        v_max = max(values.values())
        v_range = v_max - v_min

        res = {}
        for k, v in values.items():
            if v_range == 0:
                res[k] = 50.0
            else:
                norm = ((v - v_min) / v_range) * 100
                res[k] = norm if direction == RankingDirection.HIGHER_IS_BETTER else (100 - norm)
        return res

    def top_leaders(self, items: list[CrossSectionalRankItem], top_n: int) -> list[CrossSectionalRankItem]:
        return sorted(items, key=lambda x: (x.rank, x.symbol))[:top_n]

    def bottom_laggards(self, items: list[CrossSectionalRankItem], bottom_n: int) -> list[CrossSectionalRankItem]:
        return sorted(items, key=lambda x: (x.rank, x.symbol))[-bottom_n:]
