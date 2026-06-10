"""Pydantic models mirroring profile.yaml structure."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ATSBaseModel(BaseModel):
    """Base model that allows extra fields and populates by alias/name."""

    model_config = {"extra": "allow", "populate_by_name": True}


class Personal(ATSBaseModel):
    """Contact / identity information."""

    name: str
    location: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class SummaryHints(ATSBaseModel):
    """Hints the LLM uses to craft the summary paragraph."""

    experience_years: str
    seniority: str
    domains: list[str] = Field(default_factory=list)


class Skills(ATSBaseModel):
    """Skill categories — each is a flat list of keyword strings."""

    languages_frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    devops_monitoring: list[str] = Field(default_factory=list)
    ai_assisted_development: list[str] = Field(default_factory=list)
    architecture_patterns: list[str] = Field(default_factory=list)


class Bullet(ATSBaseModel):
    """A single experience bullet — loosely structured so the LLM can expand it."""

    action: str
    tech: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    outcome: Optional[str] = None
    approach: Optional[str] = None
    features: Optional[str] = None
    replaced: Optional[str] = None
    # Migration-style fields
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None


class Role(ATSBaseModel):
    """A single role held at a company."""

    title: str
    start: str
    end: str
    bullets: list[Bullet] = Field(default_factory=list)


class Experience(ATSBaseModel):
    """One company block containing one or more roles."""

    company: str
    location: str
    roles: list[Role] = Field(default_factory=list)


class Education(ATSBaseModel):
    """A single education entry."""

    institution: str
    location: str
    degree: str
    major: Optional[str] = None
    gpa: Optional[str] = None
    gpa_scale: Optional[str] = None
    percentage: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    courses: list[str] = Field(default_factory=list)


class Achievement(ATSBaseModel):
    """A single achievement or publication."""

    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    journal: Optional[str] = None
    recognition: Optional[str] = None
    link: Optional[str] = None


class Project(ATSBaseModel):
    """A side-project or open-source project."""

    name: str
    tech: list[str] = Field(default_factory=list)
    url: Optional[str] = None
    year: Optional[str] = None
    description: Optional[str] = None
    achievement: Optional[str] = None


class Profile(ATSBaseModel):
    """Top-level container aggregating the full profile.yaml."""

    personal: Personal
    summary_hints: SummaryHints
    skills: Skills
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    summary: Optional[str] = None
