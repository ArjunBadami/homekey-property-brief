"""
Real estate listing data adapter - returns mock data by normalized address.
"""
from typing import Dict, Any, Optional

def get_listing_data(normalized_address: str) -> Optional[Dict[str, Any]]:
    """
    Mock listing data based on normalized address.
    Returns current listing information, photos, and market data.
    """
    # Mock data for different addresses
    mock_data = {
        "123 main street": {
            "address": "123 Main Street",
            "square_feet": 2600,  # Slightly different from county
            "bedrooms": 3,
            "bathrooms": 2.5,  # Half bath not in county data
            "year_built": 1995,
            "lot_size": "0.25 acres",
            "property_type": "Single Family",
            "listing_price": 485000,
            "days_on_market": 12,
            "listing_date": "2024-09-15",
            "agent_name": "Sarah Johnson",
            "mls_number": "MLS123456",
            "description": "Beautiful family home with updated kitchen"
        },
        "456 oak avenue": {
            "address": "456 Oak Avenue",
            "square_feet": 1800,
            "bedrooms": 2,
            "bathrooms": 2,
            "year_built": 1988,
            "lot_size": "0.20 acres",
            "property_type": "Condo",
            "listing_price": 345000,
            "days_on_market": 45,
            "listing_date": "2024-08-01",
            "agent_name": "Mike Chen",
            "mls_number": "MLS789012",
            "description": "Modern condo with city views"
        },
        "789 pine drive": {
            "address": "789 Pine Drive",
            "square_feet": 3100,  # Different from county
            "bedrooms": 4,
            "bathrooms": 3.5,  # Half bath not in county
            "year_built": 2010,
            "lot_size": "0.42 acres",  # Slightly different
            "property_type": "Single Family",
            "listing_price": 725000,
            "days_on_market": 8,
            "listing_date": "2024-09-20",
            "agent_name": "Lisa Rodriguez",
            "mls_number": "MLS345678",
            "description": "Stunning contemporary home with pool"
        }
    }
    
    return mock_data.get(normalized_address)
