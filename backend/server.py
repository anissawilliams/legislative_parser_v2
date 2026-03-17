"""
FastAPI server for the LegParser ordinance extraction API.

Endpoints:
    POST /api/extract        – Extract structured data from ordinance text
    GET  /api/schema         – Return the current Pydantic-generated JSON schema
    GET  /api/health         – Health check
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from extractor import extract_ordinance
from models import OrdinanceDocument

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("legparser")

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="LegParser API",
    description="Extract structured data from legislative ordinance texts using Claude AI.",
    version="2.0.0",
)

# CORS – allow configurable frontend origin
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ────────────────────────────────────────────────


class ExtractionRequest(BaseModel):
    """Incoming request to extract ordinance data."""

    legislative_text: str = Field(
        ...,
        min_length=50,
        description="The full text of the ordinance to parse.",
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use for extraction.",
    )


class ValidationIssueResponse(BaseModel):
    field: str
    severity: str
    message: str


class ExtractionResponse(BaseModel):
    """Full extraction response returned to the client."""

    document: dict[str, Any]
    issues: list[ValidationIssueResponse]
    is_valid: bool
    model_used: str
    tokens_used: int
    extracted_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {
        "status": "healthy",
        "api_key_configured": has_key,
        "version": "2.0.0",
    }


@app.get("/api/schema")
async def get_schema():
    """Return the Pydantic-generated JSON schema for OrdinanceDocument."""
    return OrdinanceDocument.model_json_schema()


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract(req: ExtractionRequest):
    """
    Accept ordinance text, run LLM extraction, validate with Pydantic,
    and return the structured result.
    """
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Received extraction request: %s", req.legislative_text[:50])
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable is not set.",
        )

    try:
        result = extract_ordinance(
            req.legislative_text,
            model=req.model,
            api_key=api_key,
        )
    except Exception as exc:
        logger.exception("Extraction failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return ExtractionResponse(
        document=result.document.model_dump(),
        issues=[
            ValidationIssueResponse(
                field=i.field, severity=i.severity, message=i.message
            )
            for i in result.issues
        ],
        is_valid=result.is_valid,
        model_used=result.model_used,
        tokens_used=result.tokens_used,
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
