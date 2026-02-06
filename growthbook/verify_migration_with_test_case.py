#!/usr/bin/env python3
"""
Verify migration by comparing GrowthBook output with expected answers.

This script takes a test case folder path and:
1. Reads variations.json (variation IDs)
2. Evaluates features using GrowthBook SDK
3. Compares results with answer.json (deep comparison)
4. Saves output.json and comparison_result.txt to the test case folder

Usage:
    python verify_migration_with_test_case.py <test_case_folder>
    
Example:
    python verify_migration_with_test_case.py ../test_cases/case_1/
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
        
        # Handle ampersand or semicolon-separated conditions
        if "&" in variation_id or ";" in variation_id:
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
    feature_definitions = get_feature_definitions()
    
    if not feature_definitions:
        print("✗ No feature definitions available")
        return {}
    
    gb = GrowthBookSDK(
        api_host=API_BASE_URL,
        client_key=GROWTHBOOK_CLIENT_KEY,
        features=feature_definitions,
        attributes=attributes
    )
    
    results = {}
    
    for feature_id in sorted(feature_definitions.keys()):
        feature_result = gb.eval_feature(feature_id)
        value = feature_result.value if feature_result else None
        
        if value is not None:
            results[feature_id] = value
    
    gb.destroy()
    
    return results


def deep_compare_values(value1, value2, path=""):
    """
    Deeply compare two values recursively.
    GrowthBook stores all values as JSON arrays of strings, so we normalize
    primitives to strings before comparison.
    
    Args:
        value1: First value (from GrowthBook)
        value2: Second value (from configuration)
        path: Current path in the nested structure (for error reporting)
        
    Returns:
        tuple: (is_equal: bool, differences: list)
    """
    differences = []
    
    # Handle None values
    if value1 is None and value2 is None:
        return True, []
    if value1 is None or value2 is None:
        differences.append({
            'path': path,
            'value1': value1,
            'value2': value2,
            'reason': 'One value is None'
        })
        return False, differences
    
    # Normalize primitives to strings for comparison (GrowthBook stores everything as string)
    def normalize_primitive(val):
        """Convert primitive values to strings for comparison."""
        if isinstance(val, bool):
            # Keep booleans as-is for now
            return val
        if isinstance(val, (int, float)):
            return str(val)
        return val
    
    # If both are primitives (not dict/list), normalize and compare
    if not isinstance(value1, (dict, list)) and not isinstance(value2, (dict, list)):
        norm_val1 = normalize_primitive(value1)
        norm_val2 = normalize_primitive(value2)
        
        if norm_val1 == norm_val2:
            return True, []
        else:
            differences.append({
                'path': path,
                'value1': value1,
                'value2': value2,
                'reason': 'Values differ'
            })
            return False, differences
    
    # Handle type mismatch for complex types (dict/list)
    if type(value1) != type(value2):
        differences.append({
            'path': path,
            'value1': value1,
            'value2': value2,
            'reason': f'Type mismatch: {type(value1).__name__} vs {type(value2).__name__}'
        })
        return False, differences
    
    # Handle dictionaries - recursively compare
    if isinstance(value1, dict):
        all_keys = set(value1.keys()) | set(value2.keys())
        is_equal = True
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in value1:
                differences.append({
                    'path': current_path,
                    'value1': '<missing>',
                    'value2': value2[key],
                    'reason': 'Key missing in first value'
                })
                is_equal = False
            elif key not in value2:
                differences.append({
                    'path': current_path,
                    'value1': value1[key],
                    'value2': '<missing>',
                    'reason': 'Key missing in second value'
                })
                is_equal = False
            else:
                key_equal, key_diffs = deep_compare_values(value1[key], value2[key], current_path)
                if not key_equal:
                    is_equal = False
                    differences.extend(key_diffs)
        
        return is_equal, differences
    
    # Handle lists - compare element by element
    if isinstance(value1, list):
        if len(value1) != len(value2):
            differences.append({
                'path': path,
                'value1': value1,
                'value2': value2,
                'reason': f'List length mismatch: {len(value1)} vs {len(value2)}'
            })
            return False, differences
        
        is_equal = True
        for i, (item1, item2) in enumerate(zip(value1, value2)):
            current_path = f"{path}[{i}]"
            item_equal, item_diffs = deep_compare_values(item1, item2, current_path)
            if not item_equal:
                is_equal = False
                differences.extend(item_diffs)
        
        return is_equal, differences
    
    # Should not reach here for primitives (handled above)
    return True, []


def compare_json_objects(growthbook_data, config_data):
    """
    Compare two JSON objects deeply and return comparison results.
    
    Args:
        growthbook_data: GrowthBook evaluation results
        config_data: Expected configuration
        
    Returns:
        dict: Comparison results with statistics and differences
    """
    results = {
        'matched': [],
        'different': [],
        'missing_in_growthbook': [],
        'extra_in_growthbook': [],
        'differences_detail': []
    }
    
    # Get all keys
    all_keys = set(config_data.keys()) | set(growthbook_data.keys())
    
    for key in sorted(all_keys):
        # Check for missing keys
        if key not in growthbook_data:
            results['missing_in_growthbook'].append(key)
            continue
        
        if key not in config_data:
            results['extra_in_growthbook'].append(key)
            continue
        
        # Deep compare values
        is_equal, differences = deep_compare_values(
            growthbook_data[key], 
            config_data[key], 
            key
        )
        
        if is_equal:
            results['matched'].append(key)
        else:
            results['different'].append(key)
            results['differences_detail'].extend(differences)
    
    return results


def format_comparison_output(comparison_results, growthbook_count, config_count):
    """
    Format comparison results as a readable text output.
    
    Args:
        comparison_results: Results from compare_json_objects
        growthbook_count: Number of keys in GrowthBook data
        config_count: Number of keys in configuration data
        
    Returns:
        str: Formatted output text
    """
    lines = []
    lines.append("=" * 80)
    lines.append("MIGRATION VERIFICATION RESULTS")
    lines.append("=" * 80)
    lines.append("")
    
    # Show differences
    if comparison_results['differences_detail']:
        lines.append("DIFFERENCES FOUND:")
        lines.append("")
        for diff in comparison_results['differences_detail']:
            lines.append(f"✗ Path: {diff['path']}")
            lines.append(f"  GrowthBook: {diff['value1']}")
            lines.append(f"  Expected:   {diff['value2']}")
            lines.append(f"  Reason: {diff['reason']}")
            lines.append("")
    
    # Show missing keys
    if comparison_results['missing_in_growthbook']:
        lines.append("MISSING IN GROWTHBOOK:")
        for key in comparison_results['missing_in_growthbook']:
            lines.append(f"  ✗ {key}")
        lines.append("")
    
    # Show extra keys
    if comparison_results['extra_in_growthbook']:
        lines.append("EXTRA IN GROWTHBOOK (not in configuration):")
        for key in comparison_results['extra_in_growthbook']:
            lines.append(f"  ℹ {key}")
        lines.append("")
    
    # Summary
    lines.append("=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80)
    lines.append(f"Total keys in GrowthBook: {growthbook_count}")
    lines.append(f"Total keys in configuration: {config_count}")
    lines.append("")
    lines.append(f"✓ Matched keys: {len(comparison_results['matched'])}")
    lines.append(f"✗ Different values: {len(comparison_results['different'])}")
    lines.append(f"✗ Missing in GrowthBook: {len(comparison_results['missing_in_growthbook'])}")
    lines.append(f"ℹ Extra in GrowthBook: {len(comparison_results['extra_in_growthbook'])}")
    lines.append("")
    
    # Final verdict
    has_issues = (
        comparison_results['different'] or 
        comparison_results['missing_in_growthbook']
    )
    
    if has_issues:
        lines.append("✗ VERIFICATION FAILED - differences found")
    else:
        lines.append("✓ VERIFICATION PASSED - all values match!")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python verify_migration_with_test_case.py <test_case_folder>")
        print("")
        print("Example:")
        print("  python verify_migration_with_test_case.py ../test_cases/case_1/")
        print("")
        print("The test case folder should contain:")
        print("  - variations.json (variation IDs)")
        print("  - answer.json (expected values)")
        sys.exit(1)
    
    test_case_folder = sys.argv[1].rstrip('/')
    
    # Validate folder exists
    if not os.path.isdir(test_case_folder):
        print(f"✗ Error: Folder not found: {test_case_folder}")
        sys.exit(1)
    
    input_file = os.path.join(test_case_folder, "variations.json")
    config_file = os.path.join(test_case_folder, "answer.json")
    output_file = os.path.join(test_case_folder, "output.json")
    result_file = os.path.join(test_case_folder, "comparison_result.txt")
    
    print(f"Test case folder: {test_case_folder}")
    print("")
    
    # Step 1: Load variations.json
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            variation_ids = json.load(f)
        print(f"✓ Loaded {len(variation_ids)} variation IDs from variations.json")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {input_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {input_file}: {e}")
        sys.exit(1)
    
    # Step 2: Evaluate GrowthBook features
    print("Evaluating GrowthBook features...")
    attributes = parse_variation_ids_to_attributes(variation_ids)
    growthbook_data = evaluate_features_with_attributes(attributes)
    print(f"✓ Evaluated {len(growthbook_data)} features")
    
    # Step 3: Load answer.json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        print(f"✓ Loaded {len(config_data)} expected answers")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {config_file}: {e}")
        sys.exit(1)
    
    # Step 4: Compare results
    print("Comparing results...")
    comparison_results = compare_json_objects(growthbook_data, config_data)
    
    # Step 5: Save output.json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(growthbook_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved GrowthBook output to {output_file}")
    
    # Step 6: Format and save comparison results
    output_text = format_comparison_output(
        comparison_results, 
        len(growthbook_data), 
        len(config_data)
    )
    
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(output_text)
    print(f"✓ Saved comparison results to {result_file}")
    
    # Step 7: Display results
    print("")
    print(output_text)
    
    # Exit with appropriate code
    has_issues = (
        comparison_results['different'] or 
        comparison_results['missing_in_growthbook']
    )
    
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
