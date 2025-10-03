# Property Brief Aggregator

## Problem framing

Property information is often scattered across multiple sources, inconsistent across those sources, and incomplete. This feature aggregates data for a given address, reconciles conflicts into a canonical “Property Brief,” exposes provenance and disputes, and computes a completeness score so buyers see a clear and trustworthy snapshot.

## Architecture overview

- **Sources (scattered):** Pluggable adapters (e.g., county, listing, hoa) fetch raw payloads. Raw responses are stored as `SourceDatum` with `source_name` and `fetched_at` for audit and refresh.
- **Merge (inconsistent):** A central merge policy produces a canonical brief per field using:
  - Freshness wins (newest `fetched_at`).
  - If tie, source priority: county > listing > hoa.
  - Material variance thresholds flag disputes (e.g., square_feet delta > 5%).
  - Per-field **provenance** records the chosen source and all candidates.
- **Completeness (incomplete):** Weighted scoring across core fields. Missing fields and disputes reduce the score and are surfaced as flags.

## Data model (simplified)

- `Property`: id, normalized_address, display_address, created_at.
- `SourceDatum`: property_id, source_name, fetched_at, payload (JSON).
- `Brief`: property_id, brief JSON (canonical fields + provenance + flags), completeness, generated_at.
- `Contribution`: property_id, field, proposed_value, reason, contributor, created_at.

## Endpoints

- `POST /properties/ingest`  
  Body: `{ "address": "123 Main St, San Diego, CA" }`  
  Action: Upsert property, fetch adapters, store `SourceDatum`, merge into `Brief`.  
  Returns: `{ "id": <property_id>, "completeness": <0-100>, "flags_count": <int> }`

- `GET /properties/{id}/sources`  
  Returns raw source payloads and timestamps for transparency.

- `GET /properties/{id}/brief`  
  Returns canonical brief JSON including `provenance`, `flags`, `missing`, and `completeness`.

- `POST /properties/{id}/contributions`  
  Body: `{ "field": "square_feet", "proposed_value": "2700", "reason": "recent renovation", "contributor": "name or email" }`  
  Action: Records suggested correction or addition for human review.

- `POST /properties/{id}/ai_summary` (optional)  
  Uses the canonical brief to produce a buyer-friendly Markdown summary. Falls back to a rule-based summary if no API key.

## Conflict resolution policy

1. Freshness wins: the value from the most recent `fetched_at` takes precedence.  
2. Tie-breaker: county > listing > hoa.  
3. Dispute thresholds: for numeric fields like square_feet, a delta greater than 5% is flagged as `disputed` and all candidate values are included in provenance.

## Completeness scoring

Core fields (address, beds, baths, square_feet, price) contribute the majority of the score. Secondary fields (lot_size, year_built, taxes, hoa) contribute the remainder. Missing or disputed fields reduce the score. The score is returned with the brief so consumers can reason about data quality.

## Running and demo

```bash
python -m venv .venv && source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use the included test script to drive the demo end-to-end:

```
python test_property_brief.py
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# OpenAI API Key for AI summaries
OPENAI_API_KEY=your_openai_api_key_here
```

- `OPENAI_API_KEY` - Required for AI summaries via OpenAI API. If not provided, the system will fall back to rule-based summaries.

**Note**: The `.env` file is already included in `.gitignore` to keep your API keys secure.
