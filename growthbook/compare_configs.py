#!/usr/bin/env python3
"""
Script to compare GrowthBook results with Swag-server merged configuration.

Compares a GrowthBook results file (from test_growthbook.py) with the merged_config.json
file (from test_swag_config.py) and reports any differences.

Usage:
    python compare_configs.py <growthbook_results_file.json>
    
Examples:
    python compare_configs.py growthbook_results.json
    python compare_configs.py result.json
    
Output:
    - Prints keys that are missing in GrowthBook results
    - Prints keys with mismatched values
    - Summary of comparison results
"""

import json
import sys
from typing import Any


def parse_value_to_string(value: Any) -> str:
    """
    Parse a value to string format.
    If value is an array, convert to "<elem-1> <elem-2> ... <elem-n>"
    
    Args:
        value: Value to parse (can be string, number, array, object, etc.)
        
    Returns:
        str: String representation of the value
    """
    if value is None:
        return ""
    
    # If it's already a string, return as-is
    if isinstance(value, str):
        return value
    
    # If it's a list/array, join elements with space and wrap in angle brackets
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        # Convert each element to string and join
        elements = [str(elem) for elem in value]
        return " ".join(f"{elem}" for elem in elements)
    
    # For other types (int, float, bool, dict), convert to string
    return str(value)


def normalize_value(value: Any) -> str:
    """
    Normalize a value for comparison.
    Handles type conversions and formatting.
    
    Args:
        value: Value to normalize
        
    Returns:
        str: Normalized string value
    """
    parsed = parse_value_to_string(value)
    return parsed.strip()


def compare_configs(growthbook_file: str, merged_config_file: str = "merged_config.json"):
    """
    Compare GrowthBook results with merged Swag configuration.
    
    Args:
        growthbook_file: Path to GrowthBook results JSON file
        merged_config_file: Path to merged config JSON file (default: merged_config.json)
    """
    # Load files
    try:
        with open(growthbook_file, 'r', encoding='utf-8') as f:
            growthbook_data = json.load(f)
        print(f"✓ Loaded GrowthBook results: {growthbook_file}")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {growthbook_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {growthbook_file}: {e}")
        sys.exit(1)
    
    try:
        with open(merged_config_file, 'r', encoding='utf-8') as f:
            merged_config = json.load(f)
        print(f"✓ Loaded merged config: {merged_config_file}")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {merged_config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {merged_config_file}: {e}")
        sys.exit(1)
    
    print()
    print("="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    print()
    
    # Track statistics
    missing_keys = []
    mismatched_values = []
    matched_keys = []
    
    # Compare each key in merged_config
    for key in sorted(merged_config.keys()):
        merged_value = merged_config[key]
        
        # Check if key exists in GrowthBook results
        if key not in growthbook_data:
            missing_keys.append(key)
            print(f"✗ MISSING KEY: '{key}'")
            print(f"  Expected (Swag): {merged_value}")
            print()
            continue
        
        # Get GrowthBook value
        gb_value = growthbook_data[key]
        
        # Normalize both values for comparison
        merged_str = normalize_value(merged_value)
        gb_str = normalize_value(gb_value)
        
        # Compare values
        if merged_str != gb_str:
            mismatched_values.append({
                'key': key,
                'growthbook': gb_value,
                'swag': merged_value
            })
            print(f"✗ MISMATCH: '{key}'")
            print(f"  GrowthBook: {gb_value}")
            print(f"  Swag Config: {merged_value}")
            print()
        else:
            matched_keys.append(key)
    
    # Check for keys only in GrowthBook (not in merged_config)
    extra_keys = []
    for key in growthbook_data.keys():
        if key not in merged_config:
            extra_keys.append(key)
    
    # Print summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total keys in Swag config: {len(merged_config)}")
    print(f"Total keys in GrowthBook: {len(growthbook_data)}")
    print()
    print(f"✓ Matched keys: {len(matched_keys)}")
    print(f"✗ Missing keys (in Swag but not in GrowthBook): {len(missing_keys)}")
    print(f"✗ Mismatched values: {len(mismatched_values)}")
    print(f"ℹ Extra keys (in GrowthBook but not in Swag): {len(extra_keys)}")
    print()
    
    if extra_keys:
        print("Extra keys in GrowthBook (not in Swag config):")
        for key in sorted(extra_keys):
            print(f"  - {key}: {growthbook_data[key]}")
        print()
    
    # Exit code based on comparison results
    if missing_keys or mismatched_values:
        print("✗ Comparison FAILED - differences found")
        sys.exit(1)
    else:
        print("✓ Comparison PASSED - all values match!")
        sys.exit(0)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python compare_configs.py <growthbook_results_file.json>")
        print("")
        print("Examples:")
        print("  python compare_configs.py growthbook_results.json")
        print("  python compare_configs.py result.json")
        print("")
        print("Compares GrowthBook results with merged_config.json")
        sys.exit(1)
    
    growthbook_file = sys.argv[1]
    merged_config_file = "merged_config.json"
    
    # Optional: allow specifying merged_config file as second argument
    if len(sys.argv) >= 3:
        merged_config_file = sys.argv[2]
    
    compare_configs(growthbook_file, merged_config_file)


if __name__ == "__main__":
    main()
