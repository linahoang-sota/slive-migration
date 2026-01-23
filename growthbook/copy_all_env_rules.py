#!/usr/bin/env python3
"""
Script to copy GrowthBook feature rules from production to dev for all features.
Handles rate limiting to avoid API throttling.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROWTHBOOK_API_KEY = os.getenv("GROWTHBOOK_API_KEY")
GROWTHBOOK_API_URL = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100/api/v1")

# Rate limiting settings
REQUEST_DELAY = 2.0  # seconds between requests (increased to avoid 429 errors)


def get_all_features():
    """Get all features from GrowthBook API with pagination."""
    all_features = []
    offset = 0
    limit = 100  # Fetch more per page for efficiency
    
    while True:
        url = f"{GROWTHBOOK_API_URL}/features?limit={limit}&offset={offset}"
        try:
            response = requests.get(url, auth=(GROWTHBOOK_API_KEY, ""))
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            all_features.extend(features)
            
            print(f"  Fetched {len(features)} features (offset {offset}, total so far: {len(all_features)})")
            
            # Check if there are more pages
            if not data.get("hasMore", False):
                break
            
            offset = data.get("nextOffset", offset + limit)
            time.sleep(REQUEST_DELAY)  # Rate limiting between pages
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error getting features at offset {offset}: {e}")
            break
    
    return all_features


def get_feature(feature_id):
    """Get feature details from GrowthBook API."""
    url = f"{GROWTHBOOK_API_URL}/features/{feature_id}"
    try:
        response = requests.get(url, auth=(GROWTHBOOK_API_KEY, ""))
        response.raise_for_status()
        return response.json().get("feature")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error getting feature '{feature_id}': {e}")
        return None


def update_feature(feature_id, payload):
    """Update feature using GrowthBook API."""
    url = f"{GROWTHBOOK_API_URL}/features/{feature_id}"
    try:
        response = requests.post(url, json=payload, auth=(GROWTHBOOK_API_KEY, ""))
        response.raise_for_status()
        return response.json().get("feature")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error updating feature '{feature_id}': {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return None


def copy_environment_rules(feature_id, source_env="production", target_env="dev", verbose=True):
    """Copy rules from source environment to target environment for a feature."""
    # Get current feature
    feature = get_feature(feature_id)
    if not feature:
        if verbose:
            print(f"  ✗ Feature not found")
        return False
    
    # Rate limiting
    time.sleep(REQUEST_DELAY)
    
    # Get environments
    environments = feature.get("environments", {})
    
    # Check source environment exists
    if source_env not in environments:
        if verbose:
            print(f"  ✗ Source environment '{source_env}' not found")
        return False
    
    source_config = environments[source_env]
    source_rules = source_config.get("rules", [])
    
    # Get or create target environment config
    if target_env in environments:
        target_config = environments[target_env]
    else:
        target_config = {"enabled": True, "rules": []}
    
    target_rules = target_config.get("rules", [])
    
    # Check if rules are already the same
    if len(source_rules) == len(target_rules) == 0:
        if verbose:
            print(f"  ⊘ Both environments have no rules - skipping")
        return None  # Skip, not an error
    
    # Copy rules from source to target
    target_config["rules"] = source_rules.copy()
    environments[target_env] = target_config
    
    # Update feature
    payload = {"environments": environments}
    
    updated_feature = update_feature(feature_id, payload)
    time.sleep(REQUEST_DELAY)  # Rate limiting after update
    
    if updated_feature:
        if verbose:
            print(f"  ✓ Copied {len(source_rules)} rules from '{source_env}' to '{target_env}'")
        return True
    else:
        if verbose:
            print(f"  ✗ Failed to update")
        return False


def main():
    """Main function"""
    if not GROWTHBOOK_API_KEY:
        print("✗ Error: GROWTHBOOK_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Parse command line arguments
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    
    # Remove flags from argv to get environment names
    args = [arg for arg in sys.argv[1:] if arg not in ['--yes', '-y']]
    
    source_env = args[0] if len(args) > 0 else "production"
    # Default target environments: dev, staging, test
    target_envs = args[1:] if len(args) > 1 else ["dev", "staging", "test"]
    
    print(f"\n{'='*80}")
    print(f"Copying rules from '{source_env}' to {target_envs} for ALL features")
    print(f"Rate limit: {REQUEST_DELAY}s delay between requests")
    print(f"{'='*80}\n")
    
    # Get all features
    print("Fetching all features (this may take a while for large projects)...")
    features = get_all_features()
    
    if not features:
        print("✗ No features found")
        sys.exit(1)
    
    print(f"Found {len(features)} features\n")
    
    # Analyze which features need syncing
    print("Analyzing features...")
    features_to_sync = []
    
    for feature in features:
        feature_id = feature.get("id")
        environments = feature.get("environments", {})
        
        source_rules = environments.get(source_env, {}).get("rules", [])
        
        # Check if any target environment has rules or source has rules
        has_rules = len(source_rules) > 0
        target_rules_count = {}
        
        for target_env in target_envs:
            target_rules = environments.get(target_env, {}).get("rules", [])
            target_rules_count[target_env] = len(target_rules)
            if len(target_rules) > 0:
                has_rules = True
        
        if has_rules:
            features_to_sync.append({
                "id": feature_id,
                "source_rules": len(source_rules),
                "target_rules_count": target_rules_count
            })
    
    print(f"\nFeatures that will be processed: {len(features_to_sync)}")
    print(f"(Features with at least one rule in any environment)\n")
    
    if len(features_to_sync) == 0:
        print("No features need syncing")
        sys.exit(0)
    
    # Show summary
    print("Summary:")
    for f in features_to_sync:
        target_summary = ", ".join([f"{env}={count}" for env, count in f['target_rules_count'].items()])
        print(f"  {f['id']}: {source_env}={f['source_rules']} rules → {target_summary} rules")
    
    # Confirm before proceeding
    print(f"\n{'='*80}")
    if auto_confirm:
        print("Auto-confirmed with --yes flag")
        response = "yes"
    else:
        response = input(f"Proceed with copying rules? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Cancelled")
        sys.exit(0)
    
    # Process all features
    print(f"\n{'='*80}")
    print("Processing features...")
    print(f"{'='*80}\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, f in enumerate(features_to_sync, 1):
        feature_id = f["id"]
        print(f"[{i}/{len(features_to_sync)}] {feature_id}")
        
        feature_success = 0
        feature_skip = 0
        feature_fail = 0
        
        for target_env in target_envs:
            target_rules = f['target_rules_count'].get(target_env, 0)
            print(f"  {source_env}: {f['source_rules']} rules → {target_env}: {target_rules} rules")
            
            result = copy_environment_rules(feature_id, source_env, target_env, verbose=True)
            
            if result is True:
                feature_success += 1
            elif result is None:
                feature_skip += 1
            else:
                feature_fail += 1
        
        success_count += feature_success
        skip_count += feature_skip
        fail_count += feature_fail
        
        print()
    
    # Final summary
    print(f"{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total features processed: {len(features_to_sync)}")
    print(f"Total operations (features × {len(target_envs)} environments): {len(features_to_sync) * len(target_envs)}")
    print(f"  ✓ Successfully copied: {success_count}")
    print(f"  ⊘ Skipped (no rules): {skip_count}")
    print(f"  ✗ Failed: {fail_count}")
    print(f"{'='*80}\n")
    
    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
