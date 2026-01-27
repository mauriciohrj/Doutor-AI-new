from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable


class SourceType(str, Enum):
    GOVERNMENT = "government"
    PRIMARY = "primary"
    PARTNER = "partner"
    THIRD_PARTY = "third_party"
    USER_SUBMITTED = "user_submitted"


SOURCE_WEIGHTS = {
    SourceType.GOVERNMENT: 1.0,
    SourceType.PRIMARY: 0.9,
    SourceType.PARTNER: 0.75,
    SourceType.THIRD_PARTY: 0.6,
    SourceType.USER_SUBMITTED: 0.5,
}


@dataclass(frozen=True)
class Evidence:
    field: str
    value: str
    source_type: SourceType
    source_name: str
    observed_at: datetime
    verified: bool = False


@dataclass
class Profile:
    profile_id: str
    name: str | None = None
    emails: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    linkedin_urls: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class CanonicalField:
    value: str
    confidence: float
    supporting_sources: set[str]


@dataclass
class CanonicalProfile:
    profile_id: str
    fields: dict[str, CanonicalField] = field(default_factory=dict)
    provenance: dict[str, list[Evidence]] = field(default_factory=dict)

    def add_evidence(self, field: str, evidence: Evidence) -> None:
        self.provenance.setdefault(field, []).append(evidence)

    def list_evidence(self, field: str) -> Iterable[Evidence]:
        return self.provenance.get(field, [])


@dataclass(frozen=True)
class Alert:
    field: str
    summary: str
    severity: str
    details: dict[str, str]
