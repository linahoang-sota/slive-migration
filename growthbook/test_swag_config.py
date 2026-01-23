#!/usr/bin/env python3
"""
Test script to fetch and merge Swag-server configuration files.
Takes a list of variation IDs and fetches corresponding configuration files,
then merges them based on priority order.

Usage:
    # Run with default test cases (no arguments)
    python test_swag_config.py
    
    # Run with custom variation IDs
    python test_swag_config.py default
    python test_swag_config.py os=ios
    python test_swag_config.py country=cn beta os=android
    python test_swag_config.py "utm_campaign=test&utm_medium=email" os=ios
    
Variation ID formats supported:
    - 'default'           -> fetches default.json
    - 'beta', 'creator'   -> fetches beta.json, creator.json
    - 'country=cn'        -> fetches country=cn.json
    - 'os=ios'            -> fetches os=ios.json
    - 'utm_campaign=x'    -> fetches utm_campaign=x.json
    - 'key1=val1&key2=val2' -> fetches key1=val1.json and key2=val2.json separately

Priority Order (lowest to highest):
    default, country, country-group, os, os_version, pusher-app, flavor, utm_<param>, 
    language, forced-update, suggested-update, nsfw, authenticated, creator, currency, 
    partner, verified, ab, cohort, banned, beta, owner, client_id, country=jp
    
    - Lower priority values are overridden by higher priority values
    - Last matched rule has highest priority

Output:
    - merged_config.json: Final merged configuration
"""

import json
import sys
import requests
from typing import Dict, List, Any

# Configuration
CONFIG_SERVER_URL = "http://localhost:8000/configurations"

# Priority order (lowest to highest)
# First element = lowest priority (default) - will be overridden by others
# Last element = highest priority (country=jp) - will override all others
PRIORITY_ORDER = [
    "default",
    "country",
    "country-group",
    "os",
    "os_version",
    "pusher-app",
    "flavor",
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "utm_content",
    "utm_term",
    "language",
    "forced-update",
    "suggested-update",
    "nsfw",
    "authenticated",
    "creator",
    "currency",
    "partner",
    "verified",
    "ab",
    "cohort",
    "banned",
    "beta",
    "owner",
    "client_id",
    "country=jp"
]


def get_priority_score(variation_id: str) -> int:
    """
    Get priority score for a variation ID.
    Higher score = higher priority.
    
    Args:
        variation_id: Variation ID string (e.g., 'default', 'os=ios', 'country=jp')
        
    Returns:
        int: Priority score (higher = higher priority)
    """
    # Exact match in priority list
    if variation_id in PRIORITY_ORDER:
        return PRIORITY_ORDER.index(variation_id)
    
    # Check for key-based match (e.g., 'os=ios' matches 'os')
    if "=" in variation_id:
        key = variation_id.split("=", 1)[0]
        if key in PRIORITY_ORDER:
            return PRIORITY_ORDER.index(key)
        
        # Handle utm_* parameters
        if key.startswith("utm_") and "utm_campaign" in PRIORITY_ORDER:
            # All utm_* params have same priority, use utm_campaign as reference
            return PRIORITY_ORDER.index("utm_campaign")
    
    # Default to middle priority if not found
    return len(PRIORITY_ORDER) // 2


def fetch_config(variation_id: str) -> Dict[str, Any]:
    """
    Fetch configuration for a variation ID from the configuration server.
    
    Args:
        variation_id: Variation ID (e.g., 'default', 'os=ios')
        
    Returns:
        dict: Configuration object or empty dict if fetch fails
    """
    # Construct URL
    url = f"{CONFIG_SERVER_URL}/{variation_id}.json"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        config = response.json()
        
        print(f"  ✓ Fetched {variation_id}.json ({len(config)} keys)")
        return config
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to fetch {variation_id}.json: {e}")
        return {}


def parse_variation_ids(variation_ids: List[str]) -> List[str]:
    """
    Parse variation IDs and expand ampersand-separated conditions.
    
    Args:
        variation_ids: List of variation ID strings
        
    Returns:
        list: Expanded list of variation IDs
    """
    expanded = []
    
    for variation_id in variation_ids:
        # Handle ampersand-separated conditions (utm_campaign=x&utm_medium=y)
        if "&" in variation_id:
            parts = variation_id.split("&")
            expanded.extend(parts)
        else:
            expanded.append(variation_id)
    
    return expanded


def merge_configs(configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple configuration objects.
    Later configs override earlier configs.
    
    Args:
        configs: List of configuration dictionaries
        
    Returns:
        dict: Merged configuration
    """
    merged = {}
    
    for config in configs:
        # Deep merge - later values override earlier values
        for key, value in config.items():
            merged[key] = value
    
    return merged


def main():
    """Main function"""
    try:
        # Get variation IDs from command line or show help
        if len(sys.argv) > 1:
            variation_ids = sys.argv[1:]
        else:
            # Show help message
            print("Usage: python test_swag_config.py <variation_id1> <variation_id2> ...")
            print("")
            print("Examples:")
            print("  python test_swag_config.py default")
            print("  python test_swag_config.py os=ios")
            print("  python test_swag_config.py country=cn beta os=android")
            print("  python test_swag_config.py \\\"utm_campaign=test&utm_medium=email\\\" os=ios")
            print("")
            print("Variation ID formats:")
            print("  - 'default'           -> fetches default.json")
            print("  - 'beta', 'creator'   -> fetches beta.json, creator.json")
            print("  - 'country=cn'        -> fetches country=cn.json")
            print("  - 'os=ios'            -> fetches os=ios.json")
            print("  - 'key1=val1&key2=val2' -> fetches key1=val1.json and key2=val2.json")
            print("")
            print("Output: merged_config.json")
            return
        
        # Parse and expand variation IDs
        expanded_ids = parse_variation_ids(variation_ids)
        
        print(f"\nVariation IDs: {expanded_ids}")
        print(f"Configuration Server: {CONFIG_SERVER_URL}\n")
        
        # Fetch configurations and track with priority
        configs_with_priority = []
        
        print("Fetching configurations...")
        for variation_id in expanded_ids:
            config = fetch_config(variation_id)
            if config:
                priority = get_priority_score(variation_id)
                configs_with_priority.append({
                    'id': variation_id,
                    'priority': priority,
                    'config': config
                })
        
        print()
        
        if not configs_with_priority:
            print("✗ No configurations fetched")
            return
        
        # Sort by priority (lowest to highest)
        # This ensures lower priority configs are merged first and overridden by higher priority
        configs_with_priority.sort(key=lambda x: x['priority'])
        
        # Show merge order
        print("Merge order (priority):")
        for item in configs_with_priority:
            print(f"  {item['priority']:3d} - {item['id']}")
        print()
        
        # Extract configs in priority order
        sorted_configs = [item['config'] for item in configs_with_priority]
        
        # Merge configurations
        merged_config = merge_configs(sorted_configs)
        
        # Output results
        output_file = "merged_config.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Merged configuration saved to {output_file}")
        print(f"  Total keys: {len(merged_config)}\n")
        
        # Print merged config
        print("Merged configuration:")
        print(json.dumps(merged_config, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
