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



## Freshness and update strategy

Providers differ in capabilities, so the system supports both models to keep briefs current.

- Polling and on-demand: POST /properties/{id}/refresh re-fetches sources and re-merges the brief using the freshness-first policy.
- Webhooks: POST /webhooks/source-update accepts signed notifications (HMAC-SHA256 in X-Signature) and triggers a background refresh. This is preferred when providers can push updates.

Example webhook call (simulate locally):

```
BODY='{"property_id": 1}'
SIG=$(python - <<'PY'
import hmac, hashlib, sys
secret=b"dev-secret"
body=b'{"property_id": 1}'
print(hmac.new(secret, body, hashlib.sha256).hexdigest())
PY
)
curl -X POST http://127.0.0.1:8000/webhooks/source-update \
  -H "Content-Type: application/json" \
  -H "X-Signature: $SIG" \
  -d "$BODY"
```

## Source history and upsert behavior

SourceDatum uses an upsert strategy so only one row per (property_id, source_name) is stored. Re-ingesting or refreshing replaces the payload and fetched_at rather than appending history. This keeps the demo concise while preserving the freshness rule.

## Contextual enrichment

To mitigate incompleteness, a non-blocking neighborhood enrichment endpoint is included:
- GET /properties/{id}/neighborhood returns contextual fields such as school score, walkscore, crime index, and commute time.
- These fields are informative and not part of the completeness score in this MVP.
- A separate adapter (app/adapters/neighborhood.py) demonstrates how new providers can be added without touching core merge logic.

## AI summaries

If OPENAI_API_KEY is set, POST /properties/{id}/ai_summary produces a short buyer-facing Markdown summary from the canonical brief. If the key is not set, a rule-based summary is returned. The prompt stresses fidelity to the brief and surfaces disputes and missing fields.

## Trade-offs and approach

- Local-first for speed: FastAPI, SQLModel, SQLite. Easy to reset and reseed.
- Explicit merge policy: freshness-first, then fixed source priority. Disputes flagged, not hidden.
- Provenance and transparency: per-field provenance and raw SourceDatum for auditability.
- Human-in-the-loop: contributions are stored independently and can be treated as a high-priority source once verified.
- Minimal dependencies: background work via FastAPI BackgroundTasks. No queue in the MVP.

## What I would do with more time

- Add verification workflow for contributions and promote verified items into the merge as a first-class source.
- Introduce field-level reliability scoring per provider that decays with staleness to improve conflict resolution beyond simple priority.
- Persist limited source history with compaction and expose a timeline view of key fields and provenance.
- Add rate limiting, retries with backoff, and circuit breakers for real providers.
- Expand enrichment: schools API, crime data, walkability, flood and fire risk, insurance signals, and local permitting datasets.
- Export flows: PDF brief, email share links, and a signed link to a read-only web brief.
- Observability: structured logs, request ids, and metrics on dispute rates and completeness over time.

## Commit strategy for reviewers

Frequent, narrative commits that map to design milestones:
- models
- adapters
- ingest and merge
- brief and sources endpoints
- contributions
- AI summary
- refresh and webhook
- enrichment
- docs
