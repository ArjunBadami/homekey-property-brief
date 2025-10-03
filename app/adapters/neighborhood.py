# app/adapters/neighborhood.py
# Simple, static enrichment by normalized address; real impl would call external providers.

SAMPLE = {
    "123 main st, san diego, ca": {
        "school_score": 8,
        "walkscore": 72,
        "crime_index": "low",
        "median_commute_mins": 24,
    },
    "456 oak ave, san diego, ca": {
        "school_score": 7,
        "walkscore": 65,
        "crime_index": "moderate",
        "median_commute_mins": 27,
    },
    "789 pine dr, san diego, ca": {
        "school_score": 9,
        "walkscore": 80,
        "crime_index": "low",
        "median_commute_mins": 22,
    },
}

def fetch(normalized_address: str) -> dict | None:
    return SAMPLE.get(normalized_address)
