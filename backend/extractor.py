"""
Extraction engine: builds a structured prompt from the Pydantic schema,
calls the Anthropic API, and validates the response against the models.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import anthropic

from models import (
    ExtractionResult,
    OrdinanceDocument,
    ValidationIssue,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 12288

# ── Prompt Construction ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a legislative text extraction engine. Your ONLY job is to read the
provided ordinance text and extract structured data that conforms EXACTLY
to the JSON schema below. Follow these rules strictly:

1. ONLY extract information that is explicitly stated in the text.
2. NEVER infer, assume, or hallucinate information not present in the text.
3. If a field's information is not found in the text, use the default
   sentinel value specified in the schema (e.g. "No penalties specified.",
   ["No prohibited items specified."], etc.).
4. For the "overview" field, begin with "This ordinance ..." and write
   2-4 concise sentences covering the core prohibitions, requirements,
   exemptions, and enforcement. Do NOT include environmental findings
   or narrative background.
5. For "provisions", return 3-10 concise bullet points covering ONLY
   actionable provisions (prohibitions, requirements, exemptions,
   enforcement, penalties). Exclude findings, definitions, and background.
   SEPARATE food service ware provisions from accessory provisions.
6. For "regulatory_logic", construct structured rule objects that
   represent the regulatory logic with conditions and outcomes.
7. For all boolean "rule_signals" and "legislative_text_signals",
   set to true ONLY if the concept is explicitly referenced in the text.
8. Return ONLY valid JSON. No markdown fences, no commentary, no preamble.

CRITICAL DISTINCTION — Food Service Ware vs. Accessories:
Many ordinances regulate these DIFFERENTLY. Pay close attention:

- "Food Service Ware" = the primary containers/vessels for food:
  plates, bowls, cups, trays, food boats, boxes, hinged/lidded containers,
  clamshells, cartons. These typically have MATERIAL BANS (no polystyrene)
  and REQUIRED ALTERNATIVES (must be compostable/recyclable).

- "Food Service Ware Accessories" = supplementary items:
  utensils (forks, knives, spoons, chopsticks), straws, stirrers, lids,
  condiment packets, napkins, cup sleeves, splash sticks.
  These are typically regulated as UPON REQUEST ONLY, with UNBUNDLING
  requirements and SELF-SERVICE DISPENSER rules.

Populate "food_service_ware_rules" and "food_service_ware_accessory_rules"
as separate objects. If the ordinance does not distinguish between ware
and accessories, put all material/ban info under food_service_ware_rules
and note "Not distinguished from food service ware in this ordinance"
in the accessory rules.

THIRD-PARTY / DIGITAL PLATFORM RULES:
If the ordinance addresses third-party delivery services (DoorDash, UberEats,
etc.), digital ordering platforms, or point-of-sale defaults, capture these
under "third_party_platform_rules". Key things to look for:
- Must the digital platform default to NO accessories?
- Must the menu provide itemized/individual selection of accessories?
- Are delivery services treated differently from dine-in/takeout?

RECORD-KEEPING:
If the ordinance requires facilities to maintain purchase records, capture
the requirement, retention period, and inspection access rules under
"record_keeping_rules".

MATERIAL SIGNAL GRANULARITY:
Pay careful attention to WHICH forms of polystyrene are banned:
- "Expanded polystyrene" (EPS foam) only → set contains_expanded_polystyrene_ban = true
- ALL polystyrene (EPS + XPS + #6) → set contains_all_polystyrene_ban = true
- If the text just says "polystyrene" without specifying, set contains_polystyrene_ban = true
  and check for definitions section to determine if it covers all forms.

For alternative materials, distinguish between:
- "Compostable" (BPI-certified, ASTM D6400, etc.) → contains_compostable_requirement
- "Natural fiber" (bagasse, bamboo, wheat straw, molded fiber, etc.) → contains_natural_fiber_requirement
- "Recyclable" (accepted by curbside program) → contains_recyclable_requirement
- "Reusable" → contains_reusable_requirement
These are NOT mutually exclusive — an ordinance can require compostable AND recyclable.

EXEMPTIONS — CRITICAL, DO NOT SKIP:
Ordinances almost always include exemptions. These are frequently missed.
Look carefully for ALL of these common exemption patterns:

1. MEAT/FISH/POULTRY: "Packaging for raw meat, fish, and poultry" or similar.
   Set contains_meat_fish_poultry_exemption = true AND mentions_raw_meat_exemption,
   mentions_raw_fish_exemption, mentions_raw_poultry_exemption as applicable.

2. ALUMINUM FOIL: "Disposable food service ware that is entirely aluminum
   foil-based" or similar. Set contains_aluminum_foil_exemption = true.
   Also add to food_service_ware_rules.exempt_items.

3. RECYCLABLE GLASS: "Recyclable glass" as exempt. Set
   contains_recyclable_glass_exemption = true.

4. MEDICAL/HEALTHCARE: Healthcare facilities exempt for medical purposes.
   Set contains_medical_exemption = true.

5. PRE-PACKAGED: "Pre-packaged food sealed prior to receipt" or
   "food packaged outside the facility". Set contains_prepackaged_exemption = true.

6. EMERGENCY: "Emergency disaster relief" exemptions.
   Set contains_emergency_exemption = true.

Each exemption MUST also generate a regulatory_logic rule object with
rule_type = "exemption". Example:

{{
  "rule_type": "exemption_meat_fish_poultry",
  "applicability_conditions": {{
    "all": ["item is packaging for raw meat, fish, or poultry"],
    "any": []
  }},
  "assertion_outcome": "exempt from food service ware requirements",
  "reason_template": "Packaging for raw meat, fish, and poultry is exempt per [section]."
}}

Another example for aluminum foil:
{{
  "rule_type": "exemption_aluminum_foil",
  "applicability_conditions": {{
    "all": ["disposable food service ware is entirely aluminum foil-based"],
    "any": []
  }},
  "assertion_outcome": "exempt from compostable/material requirements",
  "reason_template": "Entirely aluminum foil-based disposable food service ware is exempt per [section]."
}}

Generate one regulatory_logic rule for EACH distinct exemption found in the text.
Do not lump them together into a single rule.

JSON SCHEMA:
{schema}
"""


def _build_schema_json() -> str:
    """Generate the JSON schema from the Pydantic model."""
    schema = OrdinanceDocument.model_json_schema()
    return json.dumps(schema, indent=2)


def build_extraction_prompt(legislative_text: str) -> list[dict]:
    """Return the messages array for the API call."""
    return [
        {
            "role": "user",
            "content": (
                "Extract structured data from the following ordinance text. "
                "Return ONLY a JSON object conforming to the schema in your "
                "instructions. Do not include any text outside the JSON.\n\n"
                "--- BEGIN ORDINANCE TEXT ---\n"
                f"{legislative_text}\n"
                "--- END ORDINANCE TEXT ---"
            ),
        }
    ]


# ── Extraction ───────────────────────────────────────────────────────────────


def _clean_json_response(raw: str) -> str:
    """Strip markdown fences and leading/trailing whitespace."""
    text = raw.strip()
    # Remove ```json ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _post_validate(doc: OrdinanceDocument) -> list[ValidationIssue]:
    """Run domain-specific validation beyond Pydantic's type checks."""
    issues: list[ValidationIssue] = []

    if doc.ordinance_number == "Not specified":
        issues.append(ValidationIssue(
            field="ordinance_number",
            severity="warning",
            message="Ordinance number was not extracted. Check if text contains an ordinance identifier.",
        ))

    if doc.jurisdiction == "Not specified":
        issues.append(ValidationIssue(
            field="jurisdiction",
            severity="warning",
            message="Jurisdiction was not extracted.",
        ))

    if doc.effective_date == "Not specified":
        issues.append(ValidationIssue(
            field="effective_date",
            severity="warning",
            message="Effective date was not extracted.",
        ))

    if not doc.overview or doc.overview == "No overview available.":
        issues.append(ValidationIssue(
            field="overview",
            severity="warning",
            message="Overview is empty or default.",
        ))

    if doc.provisions == ["No actionable provisions identified."]:
        issues.append(ValidationIssue(
            field="provisions",
            severity="warning",
            message="No provisions were extracted.",
        ))

    # Check rule_signals consistency with extracted data
    if doc.rule_signals.contains_polystyrene_ban:
        has_polystyrene = any(
            "polystyrene" in item.lower() or "styrofoam" in item.lower() or "eps" in item.lower()
            for item in doc.prohibited_items
        ) or any(
            "polystyrene" in item.lower() or "styrofoam" in item.lower()
            for item in doc.food_service_ware_rules.prohibited_materials
        )
        if not has_polystyrene:
            issues.append(ValidationIssue(
                field="rule_signals.contains_polystyrene_ban",
                severity="warning",
                message="Polystyrene ban signal is true but no polystyrene found in prohibited_items or food_service_ware_rules.",
            ))

    if doc.rule_signals.contains_pfas_ban:
        has_pfas = any(
            "pfas" in item.lower() or "fluorinated" in item.lower() or "pfoa" in item.lower()
            for item in doc.prohibited_items
        ) or "pfas" in doc.food_service_ware_rules.pfas_requirement.lower()
        if not has_pfas:
            issues.append(ValidationIssue(
                field="rule_signals.contains_pfas_ban",
                severity="warning",
                message="PFAS ban signal is true but no PFAS reference found in extracted data.",
            ))

    # Cross-check: upon_request signal vs accessory rules
    if doc.rule_signals.contains_upon_request_rule:
        if doc.food_service_ware_accessory_rules.upon_request_rule == "Not specified":
            issues.append(ValidationIssue(
                field="food_service_ware_accessory_rules.upon_request_rule",
                severity="warning",
                message="Upon-request signal is true but no upon_request_rule was extracted in accessory rules.",
            ))

    # Cross-check: third-party platform signal vs rules
    if doc.rule_signals.contains_third_party_platform_rules:
        tpr = doc.third_party_platform_rules
        if tpr.delivery_service_rules == "Not specified" and tpr.digital_ordering_default == "Not specified":
            issues.append(ValidationIssue(
                field="third_party_platform_rules",
                severity="warning",
                message="Third-party platform signal is true but no platform rules were extracted.",
            ))

    # Cross-check: record keeping signal vs rules
    if doc.rule_signals.contains_record_keeping_rules:
        if doc.record_keeping_rules.record_requirement == "Not specified":
            issues.append(ValidationIssue(
                field="record_keeping_rules",
                severity="warning",
                message="Record-keeping signal is true but no record requirement was extracted.",
            ))

    # Cross-check: polystyrene ban granularity
    if doc.rule_signals.contains_expanded_polystyrene_ban and doc.rule_signals.contains_all_polystyrene_ban:
        issues.append(ValidationIssue(
            field="rule_signals",
            severity="warning",
            message="Both expanded_polystyrene_ban and all_polystyrene_ban are true. Usually only one applies — check the ordinance definitions.",
        ))

    # Cross-check: exemption signals vs exemptions list and regulatory_logic
    exemption_checks = [
        ("contains_meat_fish_poultry_exemption", ["meat", "fish", "poultry"], "meat/fish/poultry"),
        ("contains_aluminum_foil_exemption", ["aluminum", "aluminium", "foil"], "aluminum foil"),
        ("contains_recyclable_glass_exemption", ["recyclable glass", "glass"], "recyclable glass"),
        ("contains_medical_exemption", ["medical", "healthcare", "health care"], "medical/healthcare"),
        ("contains_prepackaged_exemption", ["pre-packaged", "prepackaged", "pre-sealed", "sealed prior"], "pre-packaged food"),
        ("contains_emergency_exemption", ["emergency", "disaster"], "emergency/disaster relief"),
    ]

    all_exemption_text = " ".join(doc.exemptions).lower()
    all_exempt_items = " ".join(doc.food_service_ware_rules.exempt_items).lower()
    logic_types = [r.rule_type.lower() for r in doc.regulatory_logic]

    for signal_name, keywords, label in exemption_checks:
        if getattr(doc.rule_signals, signal_name, False):
            found_in_text = any(kw in all_exemption_text or kw in all_exempt_items for kw in keywords)
            if not found_in_text:
                issues.append(ValidationIssue(
                    field=f"rule_signals.{signal_name}",
                    severity="warning",
                    message=f"{label} exemption signal is true but not found in exemptions or exempt_items lists.",
                ))
            found_in_logic = any(f"exemption" in lt and any(kw in lt for kw in keywords) for lt in logic_types)
            if not found_in_logic:
                issues.append(ValidationIssue(
                    field="regulatory_logic",
                    severity="warning",
                    message=f"{label} exemption signal is true but no corresponding exemption rule found in regulatory_logic.",
                ))

    return issues


def extract_ordinance(
    legislative_text: str,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Run the full extraction pipeline:
      1. Build prompt from Pydantic schema
      2. Call Claude API
      3. Parse and validate response
      4. Run post-validation checks
      5. Return structured ExtractionResult
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is required.")

    client = anthropic.Anthropic(api_key=key)

    schema_json = _build_schema_json()
    system = SYSTEM_PROMPT.format(schema=schema_json)
    messages = build_extraction_prompt(legislative_text)

    logger.info("Calling %s for extraction…", model)

    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    )

    raw_text = response.content[0].text
    cleaned = _clean_json_response(raw_text)

    tokens_used = (
        (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
    )

    # ── Parse JSON ───────────────────────────────────────────────────────
    try:
        raw_json: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned invalid JSON: %s", exc)
        return ExtractionResult(
            document=OrdinanceDocument(),
            raw_json={},
            issues=[ValidationIssue(
                field="__root__",
                severity="error",
                message=f"LLM returned invalid JSON: {exc}",
            )],
            model_used=model,
            tokens_used=tokens_used,
        )

    # ── Validate with Pydantic ───────────────────────────────────────────
    try:
        doc = OrdinanceDocument.model_validate(raw_json)
    except Exception as exc:
        logger.error("Pydantic validation failed: %s", exc)
        return ExtractionResult(
            document=OrdinanceDocument(),
            raw_json=raw_json,
            issues=[ValidationIssue(
                field="__root__",
                severity="error",
                message=f"Schema validation error: {exc}",
            )],
            model_used=model,
            tokens_used=tokens_used,
        )

    # ── Post-validation ──────────────────────────────────────────────────
    issues = _post_validate(doc)

    return ExtractionResult(
        document=doc,
        raw_json=raw_json,
        issues=issues,
        model_used=model,
        tokens_used=tokens_used,
    )