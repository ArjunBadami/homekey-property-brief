import re
import requests
from datetime import datetime, timezone
from typing import Dict, Any

def normalize_address(address: str) -> str:
    """
    Normalize address for consistent lookup across sources.
    Converts to lowercase, removes extra whitespace, standardizes abbreviations.
    """
    if not address:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = address.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Standardize common abbreviations
    replacements = {
        r'\bst\b': 'street',
        r'\bave\b': 'avenue',
        r'\bblvd\b': 'boulevard',
        r'\bdr\b': 'drive',
        r'\brd\b': 'road',
        r'\bln\b': 'lane',
        r'\bct\b': 'court',
        r'\bpl\b': 'place',
        r'\bapt\b': 'apartment',
        r'\bunit\b': '#',
        r'\b#\s*': '#',
        r'\.': '',  # Remove periods
        r',': '',   # Remove commas
    }
    
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    return normalized.strip()

def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)

def merge_source_data(sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge data from multiple sources with conflict resolution.
    Priority: freshness > listing > county > hoa
    For disputes >5% in square footage, mark as conflicting.
    """
    if not sources:
        return {}
    
    # Define source priority (higher number = higher priority)
    source_priority = {
        'listing': 3,
        'county': 2, 
        'hoa': 1
    }
    
    merged = {}
    provenance = {}
    conflicts = []
    
    # Get all field names across all sources
    all_fields = set()
    for source_data in sources.values():
        all_fields.update(source_data.keys())
    
    for field in all_fields:
        field_values = {}
        
        # Collect values from all sources that have this field
        for source_name, source_data in sources.items():
            if field in source_data:
                field_values[source_name] = source_data[field]
        
        if not field_values:
            continue
            
        # If only one source has the value, use it
        if len(field_values) == 1:
            source_name = list(field_values.keys())[0]
            merged[field] = field_values[source_name]
            provenance[field] = source_name
            continue
            
        # Multiple sources have values - need conflict resolution
        if field == 'square_feet':
            # Special handling for square footage conflicts >5%
            values = list(field_values.values())
            if len(values) >= 2:
                try:
                    numeric_values = [float(v) for v in values if str(v).replace('.', '').isdigit()]
                    if len(numeric_values) >= 2:
                        min_val = min(numeric_values)
                        max_val = max(numeric_values)
                        if max_val > 0 and (max_val - min_val) / max_val > 0.05:  # >5% difference
                            conflicts.append({
                                'field': field,
                                'values': field_values,
                                'reason': 'Square footage varies by more than 5%'
                            })
                except (ValueError, TypeError):
                    pass
        
        # Choose value based on source priority
        best_source = max(field_values.keys(), key=lambda x: source_priority.get(x, 0))
        merged[field] = field_values[best_source]
        provenance[field] = best_source
    
    # Add metadata
    merged['_metadata'] = {
        'provenance': provenance,
        'conflicts': conflicts,
        'sources_used': list(sources.keys()),
        'merged_at': now_utc().isoformat()
    }
    
    return merged

def calculate_completeness_score(brief_data: Dict[str, Any]) -> int:
    """
    Calculate completeness score (0-100) based on available fields.
    Core fields: address, square_feet, bedrooms, bathrooms, year_built
    """
    core_fields = ['address', 'square_feet', 'bedrooms', 'bathrooms', 'year_built']
    optional_fields = ['lot_size', 'property_type', 'hoa_fee', 'tax_assessed_value']
    
    available_core = sum(1 for field in core_fields if field in brief_data and brief_data[field] is not None)
    available_optional = sum(1 for field in optional_fields if field in brief_data and brief_data[field] is not None)
    
    # Core fields are worth 15 points each (75 total), optional fields 5 points each (25 total)
    score = (available_core * 15) + (available_optional * 5)
    return min(score, 100)

def budget(messages, want_max_tokens=2500):
    """Calculate max_tokens based on message content length"""
    # Simple token estimation: ~4 characters per token
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    estimated_tokens = total_chars // 4
    
    # Return the smaller of estimated tokens or desired max tokens
    return min(estimated_tokens, want_max_tokens)

def call_llm_topics(prompt: str) -> str:
    from .config import settings
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    OPENAI_API_HEADERS = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}

    messages = [
        {"role":"system","content":"You are a helpful real estate property brief summarizer, which takes in the property brief json (which is aggregation of several sources: hoa, listing, county data), and generates a brief for potential buyers. Also included are some contributions of the property which have been added by other users who have seen the property, so in your output, mention these contributions with a grain of salt, especially if they are negative."},
        {"role":"user","content": prompt}
    ]
    max_tokens = budget(messages, want_max_tokens=2500)

    body = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.15,
        "top_p": 0.9,
        "max_tokens": max_tokens
    }
    
    try:
        print(f"Making OpenAI API call with {max_tokens} max tokens...")
        r = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=OPENAI_API_HEADERS, timeout=60)
        
        print(f"Response status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"Error response text: {r.text}")
            r.raise_for_status()
        
        response_data = r.json()
        print(f"Response keys: {list(response_data.keys())}")
        
        if "choices" not in response_data:
            raise KeyError(f"'choices' not found in response. Available keys: {list(response_data.keys())}")
        
        if not response_data["choices"]:
            raise KeyError("'choices' array is empty")
        
        choice = response_data["choices"][0]
        if "message" not in choice:
            raise KeyError(f"'message' not found in choice. Available keys: {list(choice.keys())}")
        
        if "content" not in choice["message"]:
            raise KeyError(f"'content' not found in message. Available keys: {list(choice['message'].keys())}")
        
        return choice["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        raise
    except KeyError as e:
        print(f"Key error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
