"""
HOA data adapter - returns mock data by normalized address.
"""
from typing import Dict, Any, Optional

def get_hoa_data(normalized_address: str) -> Optional[Dict[str, Any]]:
    """
    Mock HOA data based on normalized address.
    Returns HOA fees, rules, and community information.
    """
    # Mock data for different addresses
    mock_data = {
        "123 main street": {
            "address": "123 Main Street",
            "hoa_name": "Main Street Community Association",
            "hoa_fee": 0,  # No HOA
            "hoa_fee_frequency": "N/A",
            "hoa_contact": "N/A",
            "amenities": [],
            "restrictions": []
        },
        "456 oak avenue": {
            "address": "456 Oak Avenue",
            "hoa_name": "Oak Gardens Condo Association",
            "hoa_fee": 285,
            "hoa_fee_frequency": "monthly",
            "hoa_contact": "oakgardens@hoa.com",
            "amenities": ["Pool", "Fitness Center", "Parking Garage"],
            "restrictions": ["No pets over 25lbs", "Rental restrictions apply"],
            "special_assessments": [
                {"date": "2024-01-15", "amount": 1200, "reason": "Roof replacement"}
            ]
        },
        "789 pine drive": {
            "address": "789 Pine Drive", 
            "hoa_name": "Pine Ridge Homeowners Association",
            "hoa_fee": 150,
            "hoa_fee_frequency": "monthly",
            "hoa_contact": "pineridge@hoa.com",
            "amenities": ["Community Pool", "Tennis Courts", "Walking Trails"],
            "restrictions": ["Architectural approval required", "No commercial vehicles"],
            "special_assessments": []
        }
    }
    
    return mock_data.get(normalized_address)
