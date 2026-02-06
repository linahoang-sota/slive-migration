#!/usr/bin/env python3
"""
Script to evaluate GrowthBook features with variation IDs.
Takes a JSON file containing variation IDs (Swag-server format) and returns matched feature values.

Usage:
    python get_growthbook_values.py <input.json> <output.json>
    
Arguments:
    input.json  - JSON file containing array of variation IDs
    output.json - Output file for GrowthBook evaluation results
    
Variation ID formats supported:
    - 'default'           -> {} (empty attributes)
    - 'beta', 'creator'   -> {'is_beta': 'true', 'is_creator': 'true'}
    - 'country=cn'        -> {'country': 'cn'}
    - 'os=ios'            -> {'os': 'ios'}
    - 'key1=val1&key2=val2' -> {'key1': 'val1', 'key2': 'val2'}

Example:
    python get_growthbook_values.py input.json output.json
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
    
    for feature_id in sorted(feature_definitions.keys()):
        # Evaluate feature
        feature_result = gb.eval_feature(feature_id)
        
        value = feature_result.value if feature_result else None
        
        # Store result - only include value in results
        if value is not None:
            results[feature_id] = value
    
    # Cleanup
    gb.destroy()
    
    return results


def main():
    """Main function"""
    # Check for correct number of arguments
    if len(sys.argv) != 3:
        print("Usage: python get_growthbook_values.py <input.json> <output.json>")
        print("")
        print("Arguments:")
        print("  input.json  - JSON file containing array of variation IDs")
        print("  output.json - Output file for GrowthBook evaluation results")
        print("")
        print("Variation ID formats:")
        print("  - 'default'           -> {} (empty attributes)")
        print("  - 'beta', 'creator'   -> {'is_beta': 'true', 'is_creator': 'true'}")
        print("  - 'country=cn'        -> {'country': 'cn'}")
        print("  - 'os=ios'            -> {'os': 'ios'}")
        print("  - 'key1=val1&key2=val2' -> {'key1': 'val1', 'key2': 'val2'}")
        print("")
        print("Example:")
        print("  python get_growthbook_values.py ../test_cases/case_1/variations.json output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # Load variation IDs from JSON file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Expect array of variation IDs
                if isinstance(data, list):
                    variation_ids = data
                else:
                    print(f"Error: {input_file} should contain an array of variation IDs")
                    sys.exit(1)
            print(f"✓ Loaded {len(variation_ids)} variation IDs from {input_file}")
        except FileNotFoundError:
            print(f"Error: File not found: {input_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {input_file}: {e}")
            sys.exit(1)
        
        # Parse variation IDs to attributes
        attributes = parse_variation_ids_to_attributes(variation_ids)
        
        # Evaluate features
        results = evaluate_features_with_attributes(attributes)
        
        # Output results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"\n✗ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
