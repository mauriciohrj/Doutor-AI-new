from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from .models import Profile


@dataclass
class DedupMatch:
    left_id: str
    right_id: str
    reason: str
    score: float


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_domain(domain: str) -> str:
    return domain.strip().lower()


def _normalize_linkedin(url: str) -> str:
    return url.strip().lower().rstrip("/")


def _name_similarity(name_a: str | None, name_b: str | None) -> float:
    if not name_a or not name_b:
        return 0.0
    cleaned_a = " ".join(name_a.lower().split())
    cleaned_b = " ".join(name_b.lower().split())
    return SequenceMatcher(None, cleaned_a, cleaned_b).ratio()


def deduplicate_profiles(profiles: Iterable[Profile]) -> list[DedupMatch]:
    profiles_list = list(profiles)
    email_index: dict[str, str] = {}
    linkedin_index: dict[str, str] = {}
    domain_index: dict[str, list[str]] = {}
    matches: list[DedupMatch] = []

    for profile in profiles_list:
        for email in profile.emails:
            normalized = _normalize_email(email)
            if normalized in email_index:
                matches.append(
                    DedupMatch(
                        left_id=email_index[normalized],
                        right_id=profile.profile_id,
                        reason=f"shared_email:{normalized}",
                        score=1.0,
                    )
                )
            else:
                email_index[normalized] = profile.profile_id

        for url in profile.linkedin_urls:
            normalized = _normalize_linkedin(url)
            if normalized in linkedin_index:
                matches.append(
                    DedupMatch(
                        left_id=linkedin_index[normalized],
                        right_id=profile.profile_id,
                        reason=f"shared_linkedin:{normalized}",
                        score=1.0,
                    )
                )
            else:
                linkedin_index[normalized] = profile.profile_id

        for domain in profile.domains:
            normalized = _normalize_domain(domain)
            domain_index.setdefault(normalized, []).append(profile.profile_id)

    for domain, profile_ids in domain_index.items():
        if len(profile_ids) < 2:
            continue
        for i in range(len(profile_ids)):
            for j in range(i + 1, len(profile_ids)):
                matches.append(
                    DedupMatch(
                        left_id=profile_ids[i],
                        right_id=profile_ids[j],
                        reason=f"shared_domain:{domain}",
                        score=0.6,
                    )
                )

    for i in range(len(profiles_list)):
        for j in range(i + 1, len(profiles_list)):
            profile_a = profiles_list[i]
            profile_b = profiles_list[j]
            similarity = _name_similarity(profile_a.name, profile_b.name)
            if similarity >= 0.9:
                matches.append(
                    DedupMatch(
                        left_id=profile_a.profile_id,
                        right_id=profile_b.profile_id,
                        reason="similar_name",
                        score=similarity,
                    )
                )

    return matches
