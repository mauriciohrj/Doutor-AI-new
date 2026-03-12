from __future__ import annotations

from collections import Counter
from typing import Iterable

from .models import Alert, CanonicalProfile, Evidence


def detect_inconsistencies(
    canonical_profile: CanonicalProfile,
    evidences: Iterable[Evidence],
    confidence_threshold: float = 0.7,
) -> list[Alert]:
    alerts: list[Alert] = []
    by_field: dict[str, list[Evidence]] = {}
    for evidence in evidences:
        by_field.setdefault(evidence.field, []).append(evidence)

    for field, field_evidence in by_field.items():
        value_counts = Counter(evidence.value for evidence in field_evidence)
        if len(value_counts) <= 1:
            continue
        canonical_field = canonical_profile.fields.get(field)
        if not canonical_field:
            continue
        if canonical_field.confidence < confidence_threshold:
            continue

        most_common_value, _ = value_counts.most_common(1)[0]
        if canonical_field.value != most_common_value:
            alerts.append(
                Alert(
                    field=field,
                    summary=f"Inconsistência em {field}",
                    severity="high",
                    details={
                        "canonical": canonical_field.value,
                        "observed_top": most_common_value,
                        "confiança": f"{canonical_field.confidence:.2f}",
                    },
                )
            )
            continue

        differing_values = [value for value in value_counts if value != canonical_field.value]
        if differing_values:
            alerts.append(
                Alert(
                    field=field,
                    summary=f"Valores divergentes em {field}",
                    severity="medium",
                    details={
                        "canonical": canonical_field.value,
                        "divergentes": ", ".join(sorted(differing_values)),
                    },
                )
            )

    return alerts
