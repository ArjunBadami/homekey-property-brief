import re
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
