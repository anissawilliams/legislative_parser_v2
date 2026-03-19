"""
Pydantic models for the Ordinance Document Schema.

These models enforce strict validation on all extracted data,
ensuring the LLM output conforms to the expected structure.

Key distinctions:
  - "Food Service Ware" = plates, bowls, cups, trays, containers, etc.
  - "Food Service Ware Accessories" = utensils, straws, stirrers, lids,
    condiment packets, napkins, etc.
  - These have DIFFERENT regulatory treatment (accessories are often
    "upon request only" while ware has material bans/alternatives).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Rule Signals ─────────────────────────────────────────────────────────────

class RuleSignals(BaseModel):
    """Boolean flags indicating which rule types appear in the ordinance."""

    # ── material bans (granular) ────────────────────────────────────────
    contains_polystyrene_ban: bool = Field(
        default=False,
        description="True if ANY polystyrene is banned (EPS, XPS, #6, or all).",
    )
    contains_expanded_polystyrene_ban: bool = Field(
        default=False,
        description="True if ONLY expanded polystyrene (EPS foam) is banned, not all polystyrene.",
    )
    contains_all_polystyrene_ban: bool = Field(
        default=False,
        description="True if ALL forms of polystyrene are banned (EPS, XPS, #6).",
    )
    contains_pfas_ban: bool = Field(
        default=False,
        description="True if PFAS / fluorinated chemicals are banned in food service ware.",
    )
    contains_plastic_ban: bool = Field(
        default=False,
        description="True if single-use plastics beyond polystyrene are banned.",
    )
    contains_packaging_ban: bool = False

    # ── alternative requirements (granular) ──────────────────────────────
    contains_alternative_requirement: bool = Field(
        default=False,
        description="True if ANY alternative material is required.",
    )
    contains_compostable_requirement: bool = Field(
        default=False,
        description="True if compostable/BPI-certified alternatives are required.",
    )
    contains_recyclable_requirement: bool = Field(
        default=False,
        description="True if recyclable alternatives are required.",
    )
    contains_reusable_requirement: bool = Field(
        default=False,
        description="True if reusable alternatives are required or encouraged.",
    )
    contains_natural_fiber_requirement: bool = Field(
        default=False,
        description="True if natural-fiber foodware (bagasse, bamboo, wheat straw, etc.) is required or referenced.",
    )

    # ── exemption signals ────────────────────────────────────────────────
    contains_meat_fish_poultry_exemption: bool = Field(
        default=False,
        description="True if raw meat, fish, or poultry packaging is explicitly exempt.",
    )
    contains_medical_exemption: bool = Field(
        default=False,
        description="True if healthcare/medical facilities are exempt.",
    )
    contains_prepackaged_exemption: bool = Field(
        default=False,
        description="True if pre-packaged food sealed before receipt is exempt.",
    )
    contains_aluminum_foil_exemption: bool = Field(
        default=False,
        description="True if aluminum foil-based ware is explicitly exempt.",
    )
    contains_recyclable_glass_exemption: bool = Field(
        default=False,
        description="True if recyclable glass is explicitly exempt.",
    )
    contains_emergency_exemption: bool = Field(
        default=False,
        description="True if emergency/disaster relief food distribution is exempt.",
    )

    # ── operational rules ────────────────────────────────────────────────
    contains_upon_request_rule: bool = False
    contains_labeling_requirement: bool = False
    contains_operational_requirement: bool = False
    contains_food_ware_rules: bool = False
    contains_accessory_rules: bool = False
    contains_third_party_platform_rules: bool = False
    contains_record_keeping_rules: bool = False
    contains_unbundling_requirement: bool = False
    contains_self_service_dispenser_rules: bool = False
    contains_digital_ordering_default: bool = False


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
    mentions_drive_through: bool = False
    mentions_takeout_delivery: bool = False
    mentions_third_party_delivery: bool = False
    mentions_digital_platforms: bool = False
    mentions_record_keeping: bool = False
    mentions_inspection_rights: bool = False
    mentions_aluminum_foil: bool = False
    mentions_recyclable_glass: bool = False
    mentions_self_service_dispensers: bool = False
    mentions_unbundled_distribution: bool = False

    # ── material-specific mentions ───────────────────────────────────────
    mentions_expanded_polystyrene: bool = Field(default=False, description="Mentions EPS or expanded polystyrene specifically.")
    mentions_extruded_polystyrene: bool = Field(default=False, description="Mentions XPS or extruded polystyrene.")
    mentions_polystyrene_6: bool = Field(default=False, description="Mentions polystyrene #6 / PS6.")
    mentions_pfas: bool = Field(default=False, description="Mentions PFAS, PFOA, PFOS, or fluorinated compounds.")
    mentions_bpi_certification: bool = Field(default=False, description="Mentions BPI certification for compostable items.")
    mentions_compostable: bool = Field(default=False, description="Mentions compostable as an alternative material.")
    mentions_recyclable: bool = Field(default=False, description="Mentions recyclable as an alternative material.")
    mentions_reusable: bool = Field(default=False, description="Mentions reusable alternatives.")
    mentions_natural_fiber: bool = Field(default=False, description="Mentions natural fiber, bagasse, bamboo, wheat straw, or similar materials.")

    # ── exemption-specific mentions ──────────────────────────────────────
    mentions_raw_meat_exemption: bool = Field(default=False, description="Mentions exemption for raw meat packaging.")
    mentions_raw_fish_exemption: bool = Field(default=False, description="Mentions exemption for raw fish packaging.")
    mentions_raw_poultry_exemption: bool = Field(default=False, description="Mentions exemption for raw poultry packaging.")
    mentions_medical_exemption: bool = Field(default=False, description="Mentions healthcare or medical facility exemption.")
    mentions_prepackaged_exemption: bool = Field(default=False, description="Mentions pre-packaged/sealed food exemption.")
    mentions_emergency_exemption: bool = Field(default=False, description="Mentions emergency/disaster relief exemption.")


# ── Applicability Conditions ─────────────────────────────────────────────────

class ApplicabilityConditions(BaseModel):
    """Conditions under which a regulatory rule applies."""

    all: list[str] = Field(default_factory=list, description="ALL of these conditions must be true.")
    any: list[str] = Field(default_factory=list, description="ANY of these conditions may trigger the rule.")


# ── Regulatory Logic Rule ────────────────────────────────────────────────────

class RegulatoryRule(BaseModel):
    """A single structured rule representing regulatory logic."""

    rule_type: str = Field(..., description=(
        "Category of rule. Common types: 'polystyrene_ban', 'pfas_ban', "
        "'food_ware_material_requirement', 'accessory_upon_request', "
        "'accessory_unbundling', 'digital_ordering_default', "
        "'self_service_dispenser', 'drive_through_exception', "
        "'third_party_platform_requirement', 'record_keeping', "
        "'inspection_access', 'exemption'."
    ))
    applicability_conditions: ApplicabilityConditions
    assertion_outcome: str = Field(..., description="What happens when the rule applies.")
    reason_template: str = Field(..., description="Human-readable explanation template.")


# ── Food Service Ware Rules (sub-model) ──────────────────────────────────────

class FoodServiceWareRules(BaseModel):
    """
    Rules specific to FOOD SERVICE WARE (plates, bowls, cups, trays,
    containers, food boats, boxes, hinged/lidded containers).
    These are the primary food-contact items — NOT accessories.
    """

    prohibited_materials: list[str] = Field(
        default_factory=lambda: ["No prohibited materials specified."],
        description=(
            "Materials banned for food service ware (e.g., 'Polystyrene-based "
            "disposable food service ware', 'EPS foam containers')."
        ),
    )
    required_alternatives: list[str] = Field(
        default_factory=lambda: ["No required alternatives specified."],
        description=(
            "What food service ware must be made of instead (e.g., "
            "'Compostable items meeting PFAS restrictions', 'BPI-certified compostable')."
        ),
    )
    covered_items: list[str] = Field(
        default_factory=lambda: ["No covered items specified."],
        description=(
            "Specific ware items covered (e.g., 'Plates', 'Bowls', 'Cups', "
            "'Food trays', 'Food boats, boxes, and hinged/lidded containers')."
        ),
    )
    pfas_requirement: str = Field(
        default="Not specified",
        description="PFAS-related requirement for food service ware, if any.",
    )
    exempt_items: list[str] = Field(
        default_factory=lambda: ["No exempt items specified."],
        description=(
            "Ware items explicitly exempt (e.g., 'Entirely aluminum foil-based "
            "disposable food service ware', 'Recyclable glass')."
        ),
    )


# ── Food Service Ware Accessory Rules (sub-model) ───────────────────────────

class FoodServiceWareAccessoryRules(BaseModel):
    """
    Rules specific to FOOD SERVICE WARE ACCESSORIES (utensils, straws,
    stirrers, lids, condiment packets, napkins, etc.).
    Often regulated differently — typically 'upon request only'.
    """

    upon_request_rule: str = Field(
        default="Not specified",
        description=(
            "The upon-request requirement for accessories. e.g., 'Accessories "
            "and standard condiments in disposable packaging shall not be "
            "provided unless specifically requested by the consumer.'"
        ),
    )
    unbundling_requirement: str = Field(
        default="Not specified",
        description=(
            "Whether accessories must be distributed unbundled / as separate "
            "individual units rather than pre-packaged bundles."
        ),
    )
    self_service_dispenser_rules: str = Field(
        default="Not specified",
        description=(
            "Rules for self-service dispensers — e.g., 'Unwrapped accessories "
            "and condiments may be available via refillable self-service "
            "dispensers that dispense one item at a time.'"
        ),
    )
    drive_through_rules: str = Field(
        default="Not specified",
        description=(
            "Special rules for drive-through or walk-in — e.g., 'May ask if "
            "consumer wants a specific accessory if necessary for consumption "
            "or to prevent spills / safely transport food.'"
        ),
    )
    covered_accessories: list[str] = Field(
        default_factory=lambda: ["No covered accessories specified."],
        description=(
            "Specific accessories covered (e.g., 'Utensils (forks, knives, spoons)', "
            "'Straws', 'Stirrers', 'Lids', 'Condiment packets', 'Napkins')."
        ),
    )


# ── Third-Party Platform Rules (sub-model) ──────────────────────────────────

class ThirdPartyPlatformRules(BaseModel):
    """
    Rules governing third-party delivery services, digital ordering,
    and point-of-sale platform defaults.
    """

    delivery_service_rules: str = Field(
        default="Not specified",
        description=(
            "Requirements when using takeout food delivery services — e.g., "
            "'Must customize menu with itemized list of available accessories "
            "and condiments for consumers to proactively select.'"
        ),
    )
    digital_ordering_default: str = Field(
        default="Not specified",
        description=(
            "Default setting for digital ordering/POS platforms — e.g., "
            "'Default option shall be that no disposable food service ware "
            "accessories are requested.'"
        ),
    )
    itemized_selection_requirement: str = Field(
        default="Not specified",
        description=(
            "Whether platforms must provide itemized selection of accessories "
            "and condiments, including different types of utensils."
        ),
    )


# ── Record Keeping Rules (sub-model) ────────────────────────────────────────

class RecordKeepingRules(BaseModel):
    """
    Record-keeping and inspection requirements.
    """

    record_requirement: str = Field(
        default="Not specified",
        description=(
            "What records must be kept — e.g., 'Complete and accurate records "
            "of purchase of acceptable disposable food service ware evidencing "
            "compliance.'"
        ),
    )
    retention_period: str = Field(
        default="Not specified",
        description="How long records must be kept (e.g., '3 years from date of purchase').",
    )
    inspection_access: str = Field(
        default="Not specified",
        description=(
            "Who may inspect and when — e.g., 'Available at no cost to the "
            "county during regular business hours by authorized employees.'"
        ),
    )


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
            "Describe prohibitions, requirements, exemptions, and enforcement. "
            "Distinguish between food service ware rules and accessory rules."
        ),
    )

    # ── establishments ───────────────────────────────────────────────────
    covered_establishments: list[str] = Field(
        default_factory=lambda: ["No covered establishments specified."],
        description=(
            "Types of establishments covered. Distinguish between food facilities, "
            "city facilities, contractors, event vendors, etc."
        ),
    )

    # ── FOOD SERVICE WARE (the key distinction) ──────────────────────────
    food_service_ware_rules: FoodServiceWareRules = Field(
        default_factory=FoodServiceWareRules,
        description=(
            "Rules specific to food service ware items (plates, bowls, cups, "
            "trays, containers). Material bans, required alternatives, exemptions."
        ),
    )

    # ── FOOD SERVICE WARE ACCESSORIES (the other key distinction) ────────
    food_service_ware_accessory_rules: FoodServiceWareAccessoryRules = Field(
        default_factory=FoodServiceWareAccessoryRules,
        description=(
            "Rules specific to accessories (utensils, straws, stirrers, lids, "
            "condiments). Upon-request rules, unbundling, dispensers."
        ),
    )

    # ── THIRD-PARTY / DIGITAL PLATFORMS ──────────────────────────────────
    third_party_platform_rules: ThirdPartyPlatformRules = Field(
        default_factory=ThirdPartyPlatformRules,
        description=(
            "Rules for third-party delivery services and digital ordering "
            "platforms — default settings, itemized selection, etc."
        ),
    )

    # ── RECORD KEEPING ───────────────────────────────────────────────────
    record_keeping_rules: RecordKeepingRules = Field(
        default_factory=RecordKeepingRules,
        description="Record-keeping and inspection requirements.",
    )

    # ── legacy flat fields (still useful for simpler ordinances) ─────────
    prohibited_items: list[str] = Field(
        default_factory=lambda: ["No prohibited items specified."],
        description="All prohibited items/materials (flat list across ware + accessories).",
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

    # ── provisions ───────────────────────────────────────────────────────
    provisions: list[str] = Field(
        default_factory=lambda: ["No actionable provisions identified."],
        description=(
            "3–10 concise actionable provisions. Separate food service ware "
            "provisions from accessory provisions. Include third-party platform "
            "rules and record-keeping if present."
        ),
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