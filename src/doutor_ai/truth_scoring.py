from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from .models import CanonicalField, Evidence, SourceType, SOURCE_WEIGHTS


def _recency_multiplier(observed_at: datetime, now: datetime) -> float:
    days_old = max((now - observed_at).days, 0)
    if days_old <= 30:
        return 1.0
    if days_old <= 180:
        return 0.9
    if days_old <= 365:
        return 0.8
    return 0.7


def _verified_bonus(verified: bool) -> float:
    return 0.15 if verified else 0.0


def score_evidence(evidence: Evidence, now: datetime | None = None) -> float:
    if now is None:
        now = datetime.now(tz=timezone.utc)
    weight = SOURCE_WEIGHTS[evidence.source_type]
    return min(weight * _recency_multiplier(evidence.observed_at, now) + _verified_bonus(evidence.verified), 1.0)


def select_canonical_field(
    field: str,
    evidences: Iterable[Evidence],
    now: datetime | None = None,
) -> CanonicalField | None:
    if now is None:
        now = datetime.now(tz=timezone.utc)
    by_value: dict[str, list[Evidence]] = defaultdict(list)
    for evidence in evidences:
        by_value[evidence.value].append(evidence)
    if not by_value:
        return None

    scored: list[tuple[str, float, set[str]]] = []
    for value, value_evidence in by_value.items():
        source_names = {evidence.source_name for evidence in value_evidence}
        scores = [score_evidence(evidence, now) for evidence in value_evidence]
        avg_score = sum(scores) / len(scores)
        independence_bonus = min(0.1 * max(len(source_names) - 1, 0), 0.2)
        avg_score = min(avg_score + independence_bonus, 1.0)
        scored.append((value, avg_score, source_names))

    scored.sort(key=lambda item: item[1], reverse=True)
    top_value, top_score, top_sources = scored[0]

    authoritative_confirmed = any(
        evidence.source_type in {SourceType.GOVERNMENT, SourceType.PRIMARY} and evidence.value == top_value
        for evidence in by_value[top_value]
    )
    if len(top_sources) >= 2 or authoritative_confirmed:
        confidence = top_score
    else:
        confidence = max(top_score - 0.2, 0.0)

    return CanonicalField(value=top_value, confidence=confidence, supporting_sources=top_sources)
