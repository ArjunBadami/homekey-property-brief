"""
County assessor data adapter - returns mock data by normalized address.
"""
from typing import Dict, Any, Optional

def get_county_data(normalized_address: str) -> Optional[Dict[str, Any]]:
    """
    Mock county assessor data based on normalized address.
    Returns property tax, assessed value, and basic property details.
    """
    # Mock data for different addresses
    mock_data = {
        "123 main street": {
            "address": "123 Main Street",
            "square_feet": 2500,
            "bedrooms": 3,
            "bathrooms": 2,
            "year_built": 1995,
            "lot_size": "0.25 acres",
            "property_type": "Single Family",
            "tax_assessed_value": 450000,
            "tax_year": 2024,
            "last_sale_date": "2020-03-15",
            "last_sale_price": 420000
        },
        "456 oak avenue": {
            "address": "456 Oak Avenue", 
            "square_feet": 1800,
            "bedrooms": 2,
            "bathrooms": 2,
            "year_built": 1988,
            "lot_size": "0.20 acres",
            "property_type": "Condo",
            "tax_assessed_value": 320000,
            "tax_year": 2024,
            "last_sale_date": "2019-07-22",
            "last_sale_price": 310000
        },
        "789 pine drive": {
            "address": "789 Pine Drive",
            "square_feet": 3200,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 2010,
            "lot_size": "0.40 acres", 
            "property_type": "Single Family",
            "tax_assessed_value": 680000,
            "tax_year": 2024,
            "last_sale_date": "2022-11-08",
            "last_sale_price": 650000
        }
    }
    
    return mock_data.get(normalized_address)
