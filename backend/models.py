"""
Pydantic models for the Ordinance Document Schema.

These models enforce strict validation on all extracted data,
ensuring the LLM output conforms to the expected structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Rule Signals ─────────────────────────────────────────────────────────────

class RuleSignals(BaseModel):
    """Boolean flags indicating which rule types appear in the ordinance."""

    contains_polystyrene_ban: bool = False
    contains_pfas_ban: bool = False
    contains_packaging_ban: bool = False
    contains_upon_request_rule: bool = False
    contains_alternative_requirement: bool = False
    contains_labeling_requirement: bool = False
    contains_operational_requirement: bool = False


# ── Legislative Text Signals ─────────────────────────────────────────────────

class LegislativeTextSignals(BaseModel):
    """Boolean indicators for specific operational/enforcement concepts."""

    mentions_fee: bool = False
    mentions_charge: bool = False
    mentions_online_ordering: bool = False
    mentions_default_settings: bool = False
    mentions_meat_fish_poultry: bool = False
    mentions_special_events: bool = False
    mentions_city_facilities: bool = False
    mentions_contractors_lessees: bool = False
    mentions_packaging: bool = False
    mentions_food_providers: bool = False


# ── Applicability Conditions ─────────────────────────────────────────────────

class ApplicabilityConditions(BaseModel):
    """Conditions under which a regulatory rule applies."""

    all: list[str] = Field(default_factory=list, description="ALL of these conditions must be true.")
    any: list[str] = Field(default_factory=list, description="ANY of these conditions may trigger the rule.")


# ── Regulatory Logic Rule ────────────────────────────────────────────────────

class RegulatoryRule(BaseModel):
    """A single structured rule representing regulatory logic."""

    rule_type: str = Field(..., description="Category of rule (e.g., 'polystyrene_ban', 'upon_request').")
    applicability_conditions: ApplicabilityConditions
    assertion_outcome: str = Field(..., description="What happens when the rule applies.")
    reason_template: str = Field(..., description="Human-readable explanation template.")


# ── Ordinance Document (top-level) ───────────────────────────────────────────

class OrdinanceDocument(BaseModel):
    """
    Complete extraction result from a legislative/ordinance document.

    Every field includes a sensible default so the LLM never needs to
    fabricate data—missing information surfaces as explicit sentinel values.
    """

    # ── identifiers ──────────────────────────────────────────────────────
    ordinance_number: str = Field(
        default="Not specified",
        description="Official ordinance/law number or identifier.",
    )
    jurisdiction: str = Field(
        default="Not specified",
        description="City, county, or municipality name.",
    )
    effective_date: str = Field(
        default="Not specified",
        description="Date the ordinance takes effect.",
    )

    # ── dates ────────────────────────────────────────────────────────────
    phase_in_dates: list[str] = Field(
        default_factory=lambda: ["No phase-in dates specified."],
        description="Phased implementation dates.",
    )

    # ── overview ─────────────────────────────────────────────────────────
    overview: str = Field(
        default="No overview available.",
        description=(
            "Concise 2–4 sentence summary beginning with 'This ordinance …'. "
            "Describe prohibitions, requirements, exemptions, and enforcement."
        ),
    )

    # ── establishments & items ───────────────────────────────────────────
    covered_establishments: list[str] = Field(
        default_factory=lambda: ["No covered establishments specified."],
    )
    prohibited_items: list[str] = Field(
        default_factory=lambda: ["No prohibited items specified."],
    )
    required_alternatives: list[str] = Field(
        default_factory=lambda: ["No required alternatives specified."],
    )
    exemptions: list[str] = Field(
        default_factory=lambda: ["No exemptions specified."],
    )

    # ── enforcement ──────────────────────────────────────────────────────
    penalties: str = Field(default="No penalties specified.")
    enforcement_agency: str = Field(default="No enforcement agency specified.")

    # ── requirements ─────────────────────────────────────────────────────
    labeling_requirements: list[str] = Field(
        default_factory=lambda: ["No labeling requirements found for this ordinance."],
    )
    operational_requirements: list[str] = Field(
        default_factory=lambda: ["No operational requirements found for this ordinance."],
    )
    utensils_and_accessories_requirements: list[str] = Field(
        default_factory=lambda: ["No utensil or accessory requirements found for this ordinance."],
    )

    # ── provisions ───────────────────────────────────────────────────────
    provisions: list[str] = Field(
        default_factory=lambda: ["No actionable provisions identified."],
        description="3–8 concise actionable provisions.",
    )

    # ── SKU types ────────────────────────────────────────────────────────
    SKU_types: list[str] = Field(
        default_factory=lambda: ["No SKU types referenced."],
    )

    # ── signals ──────────────────────────────────────────────────────────
    rule_signals: RuleSignals = Field(default_factory=RuleSignals)
    legislative_text_signals: LegislativeTextSignals = Field(
        default_factory=LegislativeTextSignals,
    )

    # ── regulatory logic ─────────────────────────────────────────────────
    regulatory_logic: list[RegulatoryRule] = Field(default_factory=list)

    # ── validators ───────────────────────────────────────────────────────

    @field_validator("overview")
    @classmethod
    def overview_starts_correctly(cls, v: str) -> str:
        if v and not v.lower().startswith("this ordinance"):
            v = f"This ordinance {v[0].lower()}{v[1:]}"
        return v

    @field_validator(
        "phase_in_dates",
        "covered_establishments",
        "prohibited_items",
        "required_alternatives",
        "exemptions",
        "labeling_requirements",
        "operational_requirements",
        "utensils_and_accessories_requirements",
        "provisions",
        "SKU_types",
        mode="before",
    )
    @classmethod
    def coerce_empty_lists(cls, v: Any) -> list[str]:
        """Ensure list fields are never completely empty."""
        if not v or (isinstance(v, list) and len(v) == 0):
            return ["Not specified."]
        return v


# ── Validation Summary (returned alongside extraction) ───────────────────────

@dataclass
class ValidationIssue:
    field: str
    severity: str  # "warning" | "error"
    message: str


@dataclass
class ExtractionResult:
    """Wraps the parsed document with metadata about extraction quality."""

    document: OrdinanceDocument
    raw_json: dict
    issues: list[ValidationIssue] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "document": self.document.model_dump(),
            "issues": [
                {"field": i.field, "severity": i.severity, "message": i.message}
                for i in self.issues
            ],
            "is_valid": self.is_valid,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
        }
