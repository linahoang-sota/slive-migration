#!/usr/bin/env python3
"""
Test script to evaluate GrowthBook features with variation IDs.
Takes a list of variation IDs (Swag-server format) and returns matched feature values.

Usage:
    # Run with default test cases (no arguments)
    python test_growthbook.py
    
    # Run with custom variation IDs
    python test_growthbook.py default
    python test_growthbook.py os=ios
    python test_growthbook.py country=cn beta os=android
    python test_growthbook.py "utm_campaign=test&utm_medium=email" os=ios
    
Variation ID formats supported:
    - 'default'           -> {} (empty attributes)
    - 'beta', 'creator'   -> {'is_beta': 'true', 'is_creator': 'true'}
    - 'country=cn'        -> {'country': 'cn'}
    - 'os=ios'            -> {'os': 'ios'}
    - 'key1=val1&key2=val2' -> {'key1': 'val1', 'key2': 'val2'}

Output:
    - With arguments: growthbook_results.json
    - Without arguments: growthbook_default_values.json, growthbook_ios_values.json, growthbook_custom_values.json
"""

import os
import json
import sys
import requests
from dotenv import load_dotenv
from growthbook import GrowthBook as GrowthBookSDK

# Load environment variables
load_dotenv()

GROWTHBOOK_API_KEY = os.getenv("GROWTHBOOK_API_KEY", "secret_admin_abc123")
GROWTHBOOK_API_URL = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100/api/v1")
GROWTHBOOK_CLIENT_KEY = os.getenv("GROWTHBOOK_CLIENT_KEY", "sdk-abc123")

# Extract base URL without /api/v1 for SDK endpoint
API_BASE_URL = GROWTHBOOK_API_URL.replace('/api/v1', '')

# Simple keys that should be converted to is_<key>=true
SIMPLE_KEYS = {
    'beta', 'authenticated', 'verified', 'creator', 'curator', 
    'banned', 'nsfw', 'owner', 'default'
}


def get_all_attributes():
    """
    Get all configured attributes from GrowthBook.
    
    Returns:
        dict: Dictionary of attributes keyed by property name
    """
    url = f"{GROWTHBOOK_API_URL}/attributes"
    
    try:
        response = requests.get(url, auth=(GROWTHBOOK_API_KEY, ""))
        response.raise_for_status()
        data = response.json()
        
        # Get attributes list from response
        items = data.get("attributes", []) if isinstance(data, dict) else data
        
        # Create dictionary keyed by property name
        attributes = {item.get("property"): item for item in items}
        
        return attributes
        
    except Exception as e:
        print(f"✗ Error fetching attributes: {e}")
        return {}


def get_feature_definitions():
    """
    Get feature definitions from GrowthBook SDK endpoint.
    This is what the SDK uses to evaluate features.
    """
    sdk_url = f"{API_BASE_URL}/api/features/{GROWTHBOOK_CLIENT_KEY}"
    
    try:
        response = requests.get(sdk_url)
        response.raise_for_status()
        data = response.json()
        return data.get('features', {})
    except Exception as e:
        print(f"✗ Error getting SDK features: {e}")
        print(f"  URL: {sdk_url}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return {}


def parse_variation_ids_to_attributes(variation_ids):
    """
    Parse a list of variation IDs (Swag-server format) into GrowthBook attributes.
    
    Handles:
    - 'default' -> skip (means no special attributes)
    - 'beta', 'creator', etc. -> {'is_beta': 'true', 'is_creator': 'true'}
    - 'country=cn' -> {'country': 'cn'}
    - 'utm_campaign=x&utm_medium=y' -> {'utm_campaign': 'x', 'utm_medium': 'y'}
    - 'utm_campaign=x;utm_medium=y' -> {'utm_campaign': 'x', 'utm_medium': 'y'}
    
    Args:
        variation_ids: List of variation ID strings
        
    Returns:
        dict: Attributes dictionary for GrowthBook SDK
    """
    attributes = {}
    
    for variation_id in variation_ids:
        # Skip 'default' - it means use defaults
        if variation_id == 'default':
            continue
        
        # Handle simple keys (beta, creator, etc.)
        if variation_id in SIMPLE_KEYS:
            attribute_name = f"is_{variation_id}"
            attributes[attribute_name] = "true"
            continue
        
        # Handle ampersand or semicolon-separated conditions (utm_campaign=x&utm_medium=y or utm_campaign=x;utm_medium=y)
        if "&" in variation_id or ";" in variation_id:
            # Split by both separators
            parts = variation_id.replace(';', '&').split("&")
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    attributes[key] = value
            continue
        
        # Handle standard key=value pairs
        if "=" in variation_id:
            key, value = variation_id.split("=", 1)
            attributes[key] = value
            continue
    
    return attributes


def evaluate_features_with_attributes(attributes):
    """
    Evaluate all features with given attributes.
    
    Args:
        attributes: Dictionary of attributes for GrowthBook SDK
        
    Returns:
        dict: Feature evaluation results
    """
    # Get feature definitions
    feature_definitions = get_feature_definitions()
    
    if not feature_definitions:
        print("✗ No feature definitions available")
        return {}
    
    # Initialize GrowthBook SDK with attributes
    gb = GrowthBookSDK(
        api_host=API_BASE_URL,
        client_key=GROWTHBOOK_CLIENT_KEY,
        features=feature_definitions,
        attributes=attributes
    )
    
    results = {}
    matched_rules = 0
    default_values = 0
    
    for feature_id in sorted(feature_definitions.keys()):
        # Evaluate feature
        feature_result = gb.eval_feature(feature_id)
        
        value = feature_result.value if feature_result else None
        is_on = feature_result.on if feature_result else False
        source = feature_result.source if feature_result else "unknown"
        
        # Track if rule matched vs default
        if source == "force":
            matched_rules += 1
        elif source == "defaultValue":
            default_values += 1
        
        # Store result - only include value in results
        if value is not None:
            results[feature_id] = value
    
    # Cleanup
    gb.destroy()
    
    return results


def main():
    """Main test function"""
    try:
        # Get variation IDs from command line or show help
        if len(sys.argv) > 1:
            # Parse variation IDs from command line
            variation_ids = sys.argv[1:]
        else:
            # Show help message
            print("Usage: python test_growthbook.py <variation_id1> <variation_id2> ...")
            print("")
            print("Examples:")
            print("  python test_growthbook.py default")
            print("  python test_growthbook.py os=ios")
            print("  python test_growthbook.py country=cn beta os=android")
            print("  python test_growthbook.py \\\"utm_campaign=test&utm_medium=email\\\" os=ios")
            print("")
            print("Variation ID formats:")
            print("  - 'default'           -> {} (empty attributes)")
            print("  - 'beta', 'creator'   -> {'is_beta': 'true', 'is_creator': 'true'}")
            print("  - 'country=cn'        -> {'country': 'cn'}")
            print("  - 'os=ios'            -> {'os': 'ios'}")
            print("  - 'key1=val1&key2=val2' -> {'key1': 'val1', 'key2': 'val2'}")
            print("")
            print("Output: growthbook_results.json")
            return
        
        # Parse variation IDs to attributes
        attributes = parse_variation_ids_to_attributes(variation_ids)
        
        # Evaluate features
        results = evaluate_features_with_attributes(attributes)
        
        # Output results
        output_file = "growthbook_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"\n✗ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
