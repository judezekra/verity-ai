"""Validated request and evidence types, independent of UI and AI providers."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Extraction(BaseModel):
    """Every extracted string must be a verbatim substring of the request."""

    model_config = ConfigDict(extra="forbid", strict=True)
    claimed_sender: str | None = Field(max_length=150)
    sender_email: str | None = Field(max_length=254)
    amount_text: str | None = Field(max_length=50)
    vendor: str | None = Field(max_length=200)
    payment_account: str | None = Field(max_length=100)
    urgency_quotes: list[str] = Field(max_length=8)
    secrecy_quotes: list[str] = Field(max_length=8)
    requested_actions: list[str] = Field(max_length=8)


class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    evidence_ids: list[str] = Field(min_length=1, max_length=30)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Literal["info", "review", "alert"]
    source: str
    message: str


@dataclass
class ParsedRequest:
    extraction: Extraction
    amount_cents: int | None
    warnings: list[str] = field(default_factory=list)


@dataclass
class Investigation:
    request_text: str
    mode: str
    model: str | None
    parsed: ParsedRequest
    findings: list[Finding]
    tool_trace: list[dict]
    employee: dict | None
    vendor: dict | None
    highlights: list[str]
    elapsed_seconds: float


class InvestigationError(Exception):
    """Safe user-facing error; never carry API response bodies or secrets."""
