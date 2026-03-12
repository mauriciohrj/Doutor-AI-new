from datetime import datetime, timezone

from doutor_ai.models import Evidence, SourceType
from doutor_ai.truth_scoring import select_canonical_field


def test_select_canonical_field_prefers_authoritative() -> None:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    evidences = [
        Evidence(
            field="company",
            value="Acme",
            source_type=SourceType.PRIMARY,
            source_name="crm",
            observed_at=now,
            verified=True,
        ),
        Evidence(
            field="company",
            value="Acme",
            source_type=SourceType.THIRD_PARTY,
            source_name="enrich",
            observed_at=now,
        ),
    ]

    canonical = select_canonical_field("company", evidences, now)

    assert canonical is not None
    assert canonical.value == "Acme"
    assert canonical.confidence >= 0.7
