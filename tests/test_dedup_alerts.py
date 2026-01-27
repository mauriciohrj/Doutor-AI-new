from datetime import datetime, timezone

from doutor_ai.alerts import detect_inconsistencies
from doutor_ai.dedup import deduplicate_profiles
from doutor_ai.models import CanonicalField, CanonicalProfile, Evidence, Profile, SourceType


def test_deduplicate_profiles_by_email_and_name() -> None:
    profiles = [
        Profile(profile_id="1", name="Ana Silva", emails=["ana@example.com"]),
        Profile(profile_id="2", name="Ana  Silva", emails=["ANA@example.com"]),
    ]

    matches = deduplicate_profiles(profiles)

    assert any(match.reason.startswith("shared_email") for match in matches)
    assert any(match.reason == "similar_name" for match in matches)


def test_detect_inconsistencies_on_confident_field() -> None:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    canonical = CanonicalProfile(
        profile_id="1",
        fields={
            "role": CanonicalField(value="Doctor", confidence=0.9, supporting_sources={"crm"})
        },
    )
    evidences = [
        Evidence(
            field="role",
            value="Doctor",
            source_type=SourceType.PRIMARY,
            source_name="crm",
            observed_at=now,
        ),
        Evidence(
            field="role",
            value="Nurse",
            source_type=SourceType.THIRD_PARTY,
            source_name="enrich",
            observed_at=now,
        ),
    ]

    alerts = detect_inconsistencies(canonical, evidences, confidence_threshold=0.7)

    assert alerts
    assert alerts[0].field == "role"
