# LegParser v2

Legislative ordinance extraction engine. Paste ordinance text → extract structured data via Claude AI → validate against a strict Pydantic schema.

## Quickstart

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your key
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY

uvicorn server:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173 — the Vite dev server proxies `/api/*` to the backend automatically.

## Project Structure

```
legparser-v2/
├── backend/
│   ├── models.py          # Pydantic models (OrdinanceDocument, RuleSignals, etc.)
│   ├── extractor.py       # Prompt builder + Claude API + validation pipeline
│   ├── server.py          # FastAPI app with /api/extract, /api/schema, /api/health
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   └── main.jsx       # Entry point
│   ├── index.html
│   ├── vite.config.js     # Dev proxy to backend
│   └── package.json
└── .gitignore
```

## How It Works

1. Pydantic models in `models.py` define the extraction schema
2. `extractor.py` auto-generates a JSON schema from the models and embeds it in a Claude prompt
3. Claude extracts data, returns JSON
4. Response is validated through Pydantic + post-validation cross-checks
5. Frontend displays results in tabs: Overview, Details, Signals, Logic, Validation, Raw JSON

## Extending the Schema

Add a field to `OrdinanceDocument` in `models.py`:

```python
my_new_field: str = Field(
    default="Not specified",
    description="What to extract — this text goes into the LLM prompt.",
)
```

That's it. The prompt, validation, and API response update automatically.
# legislative_parser_v2
