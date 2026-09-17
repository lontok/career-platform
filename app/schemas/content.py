from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models import Education, Experience, Profile, Project, Skill


class ContactLink(BaseModel):
    label: str
    url: HttpUrl

    model_config = ConfigDict(extra="forbid")


class PublicProfile(BaseModel):
    full_name: str
    headline: str
    summary: str
    location: str
    target_roles: list[str]
    email: str | None = None
    contact_links: list[ContactLink] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @field_validator("target_roles", mode="before")
    @classmethod
    def _normalize_target_roles(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [role.strip() for role in value.split(",") if role.strip()]
        if isinstance(value, list):
            return value
        raise TypeError("target_roles must be a string or list of strings")

    @classmethod
    def from_profile(cls, profile: Profile) -> PublicProfile:
        contact_links: list[ContactLink] = []
        if profile.linkedin_url:
            contact_links.append(
                ContactLink(label="LinkedIn", url=profile.linkedin_url)
            )
        if profile.github_url:
            contact_links.append(ContactLink(label="GitHub", url=profile.github_url))

        return cls(
            full_name=profile.full_name,
            headline=profile.headline,
            summary=profile.summary,
            location=profile.location,
            target_roles=profile.target_roles,
            email=profile.email,
            contact_links=contact_links,
        )


class FallbackProfile(PublicProfile):
    @field_validator("contact_links")
    @classmethod
    def _require_contact_links(
        cls, value: list[ContactLink]
    ) -> list[ContactLink]:
        if not value:
            raise ValueError("Fallback profile must include at least one contact link")
        return value


class HomepageContent(BaseModel):
    profile: PublicProfile | FallbackProfile | None = None
    experiences: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    is_fallback: bool = False
    outage_message: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


def load_fallback_profile(path: Path) -> FallbackProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FallbackProfile.model_validate(payload)
