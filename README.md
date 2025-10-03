# Property Brief Aggregator

A FastAPI application that aggregates property data from multiple sources (County, Listing, HOA) into a canonical brief with conflict resolution, provenance tracking, and user contributions.

## Features

- **Multi-source data aggregation**: County assessor, real estate listings, and HOA data
- **Address normalization**: Consistent lookup across sources
- **Conflict resolution**: Priority-based merging with dispute detection
- **Completeness scoring**: 0-100 score based on available fields
- **User contributions**: Allow users to propose fixes/corrections
- **AI summaries**: OpenAI integration with rule-based fallback
- **Provenance tracking**: Know which source provided each data point

## API Endpoints

### Property Ingestion
- `POST /properties/ingest` - Ingest property data from all sources

### Data Retrieval
- `GET /properties/{id}/sources` - Get all source data for a property
- `GET /properties/{id}/brief` - Get the merged property brief
- `GET /properties/{id}/contributions` - Get user contributions

### User Contributions
- `POST /properties/{id}/contributions` - Submit a proposed correction

### AI Features
- `POST /properties/{id}/ai_summary` - Generate AI summary (requires OPENAI_API_KEY)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --reload
```

3. Test the API:
```bash
python test_property_brief.py
```

## Mock Data

The application includes mock data for these addresses:
- `123 Main Street`
- `456 Oak Avenue`
- `789 Pine Drive`

## Environment Variables

- `OPENAI_API_KEY` - Optional, enables AI summaries via OpenAI API