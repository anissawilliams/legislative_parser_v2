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
MAX_TOKENS = 8192

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
5. For "provisions", return 3-8 concise bullet points covering ONLY
   actionable provisions (prohibitions, requirements, exemptions,
   enforcement, penalties). Exclude findings, definitions, and background.
6. For "regulatory_logic", construct structured rule objects that
   represent the regulatory logic with conditions and outcomes.
7. For all boolean "rule_signals" and "legislative_text_signals",
   set to true ONLY if the concept is explicitly referenced in the text.
8. Return ONLY valid JSON. No markdown fences, no commentary, no preamble.

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
        )
        if not has_polystyrene:
            issues.append(ValidationIssue(
                field="rule_signals.contains_polystyrene_ban",
                severity="warning",
                message="Polystyrene ban signal is true but no polystyrene items found in prohibited_items.",
            ))

    if doc.rule_signals.contains_pfas_ban:
        has_pfas = any(
            "pfas" in item.lower() or "fluorinated" in item.lower() or "pfoa" in item.lower()
            for item in doc.prohibited_items
        )
        if not has_pfas:
            issues.append(ValidationIssue(
                field="rule_signals.contains_pfas_ban",
                severity="warning",
                message="PFAS ban signal is true but no PFAS items found in prohibited_items.",
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
