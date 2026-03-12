from .alerts import detect_inconsistencies
from .dedup import DedupMatch, deduplicate_profiles
from .models import Alert, CanonicalField, CanonicalProfile, Evidence, Profile, SourceType
from .truth_scoring import score_evidence, select_canonical_field

__all__ = [
    "Alert",
    "CanonicalField",
    "CanonicalProfile",
    "DedupMatch",
    "Evidence",
    "Profile",
    "SourceType",
    "deduplicate_profiles",
    "detect_inconsistencies",
    "score_evidence",
    "select_canonical_field",
]
