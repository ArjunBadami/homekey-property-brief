#!/usr/bin/env python3
"""
Test script for Property Brief functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_ingest_property():
    """Test property ingestion"""
    test_addresses = [
        "123 Main Street",
        "456 Oak Avenue", 
        "789 Pine Drive"
    ]
    
    property_ids = []
    
    for address in test_addresses:
        payload = {"address": address}
        response = requests.post(f"{BASE_URL}/properties/ingest", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            property_ids.append(data['id'])
            print(f"[OK] Ingested {address} -> Property ID: {data['id']}")
        else:
            print(f"[ERROR] Failed to ingest {address}: {response.status_code}")
    
    return property_ids

def test_get_sources(property_id):
    """Test getting source data"""
    response = requests.get(f"{BASE_URL}/properties/{property_id}/sources")
    
    if response.status_code == 200:
        sources = response.json()
        print(f"[OK] Got {len(sources)} sources for property {property_id}")
        for source in sources:
            print(f"   - {source['source_name']}: {len(source['data'])} fields")
    else:
        print(f"[ERROR] Failed to get sources: {response.status_code}")

def test_get_brief(property_id):
    """Test getting property brief"""
    response = requests.get(f"{BASE_URL}/properties/{property_id}/brief")
    
    if response.status_code == 200:
        brief = response.json()
        print(f"[OK] Got brief for property {property_id}")
        print(f"   - Completeness: {brief['completeness_score']}%")
        print(f"   - Fields: {len(brief['data'])} total")
        if '_metadata' in brief['data']:
            print(f"   - Sources: {brief['data']['_metadata']['sources_used']}")
            if brief['data']['_metadata']['conflicts']:
                print(f"   - Conflicts: {len(brief['data']['_metadata']['conflicts'])}")
    else:
        print(f"[ERROR] Failed to get brief: {response.status_code}")

def test_create_contribution(property_id):
    """Test creating a contribution"""
    payload = {
        "field": "square_feet",
        "proposed_value": "2700",
        "reason": "Recent renovation added 200 sq ft",
        "contributor": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/properties/{property_id}/contributions", json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print(f"[OK] Created contribution {data['id']} for property {property_id}")
    else:
        print(f"[ERROR] Failed to create contribution: {response.status_code}")

def test_ai_summary(property_id):
    """Test AI summary generation"""
    payload = {}
    response = requests.post(f"{BASE_URL}/properties/{property_id}/ai_summary", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Generated {data['source']} summary:")
        print(f"   {data['summary']}")
    else:
        print(f"[ERROR] Failed to generate summary: {response.status_code}")

if __name__ == "__main__":
    print("Testing Property Brief API")
    print("=" * 50)
    
    # Test health
    test_health()
    print()
    
    # Test property ingestion
    print("Testing property ingestion...")
    property_ids = test_ingest_property()
    print()
    
    if property_ids:
        # Test with first property
        property_id = property_ids[0]
        
        # Test getting sources
        print("Testing source data retrieval...")
        test_get_sources(property_id)
        print()
        
        # Test getting brief
        print("Testing brief retrieval...")
        test_get_brief(property_id)
        print()
        
        # Test creating contribution
        print("Testing contribution creation...")
        test_create_contribution(property_id)
        print()
        
        # Test AI summary
        print("Testing AI summary...")
        test_ai_summary(property_id)
        print()
    
    print("Testing complete!")
