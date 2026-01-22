#!/usr/bin/env python3
"""
Revert all changes made by migrate_to_growthbook.py

This script will:
1. Delete all feature flags created from configuration.json
2. Delete all saved groups created during migration
3. Delete all attributes created during migration
"""

import json
import requests
import os
import time
from typing import Set, List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GrowthBookReverter:
    def __init__(self, api_url: str, api_key: str, project_id: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.project_id = project_id
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def get_all_features(self) -> List[Dict]:
        """Get all features in the project."""
        try:
            all_features = []
            limit = 100
            offset = 0
            
            while True:
                response = requests.get(
                    f"{self.api_url}/features",
                    headers=self.headers,
                    params={'limit': limit, 'offset': offset}
                )
                if response.status_code == 200:
                    data = response.json()
                    features = data.get('features', [])
                    all_features.extend(features)
                    
                    # Check if there are more features to fetch
                    if not data.get('hasMore', False):
                        break
                    
                    offset += limit
                else:
                    print(f"✗ Failed to get features: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return []
            
            print(f"Found {len(all_features)} features total")
            return all_features
        except Exception as e:
            print(f"✗ Error getting features: {e}")
            return []
    
    def delete_feature(self, feature_id: str, feature_key: str) -> bool:
        """Delete a feature flag."""
        try:
            response = requests.delete(
                f"{self.api_url}/features/{feature_id}",
                headers=self.headers
            )
            
            if response.status_code in [200, 204]:
                print(f"  ✓ Deleted feature: {feature_key}")
                return True
            else:
                print(f"  ✗ Failed to delete feature {feature_key}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error deleting feature {feature_key}: {e}")
            return False
    
    def get_all_saved_groups(self) -> List[Dict]:
        """Get all saved groups."""
        try:
            all_groups = []
            limit = 100
            offset = 0
            
            while True:
                response = requests.get(
                    f"{self.api_url}/saved-groups",
                    headers=self.headers,
                    params={'limit': limit, 'offset': offset}
                )
                if response.status_code == 200:
                    data = response.json()
                    groups = data.get('savedGroups', [])
                    all_groups.extend(groups)
                    
                    # Check if there are more groups to fetch
                    if not data.get('hasMore', False):
                        break
                    
                    offset += limit
                else:
                    print(f"✗ Failed to get saved groups: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return []
            
            print(f"Found {len(all_groups)} saved groups total")
            return all_groups
        except Exception as e:
            print(f"✗ Error getting saved groups: {e}")
            return []
    
    def delete_saved_group(self, group_id: str, group_name: str) -> bool:
        """Delete a saved group."""
        try:
            response = requests.delete(
                f"{self.api_url}/saved-groups/{group_id}",
                headers=self.headers
            )
            
            if response.status_code in [200, 204]:
                print(f"  ✓ Deleted saved group: {group_name}")
                return True
            else:
                print(f"  ✗ Failed to delete saved group {group_name}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error deleting saved group {group_name}: {e}")
            return False
    
    def get_all_attributes(self) -> List[Dict]:
        """Get all attributes."""
        try:
            response = requests.get(
                f"{self.api_url}/attributes",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('attributes', [])
                print(f"Found {len(attributes)} attributes")
                return attributes
            else:
                print(f"✗ Failed to get attributes: {response.status_code}")
                print(f"  Response: {response.text}")
                return []
        except Exception as e:
            print(f"✗ Error getting attributes: {e}")
            return []
    
    def delete_attribute(self, attribute_id: str, attribute_name: str) -> bool:
        """Delete an attribute."""
        try:
            response = requests.delete(
                f"{self.api_url}/attributes/{attribute_id}",
                headers=self.headers
            )
            
            if response.status_code in [200, 204]:
                print(f"  ✓ Deleted attribute: {attribute_name}")
                return True
            else:
                print(f"  ✗ Failed to delete attribute {attribute_name}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error deleting attribute {attribute_name}: {e}")
            return False
    
    def revert_migration(self, config_feature_names: Set[str]):
        """Revert the migration by deleting features, saved groups, and attributes."""
        print("\n" + "="*60)
        print("REVERTING GROWTHBOOK MIGRATION")
        print("="*60)
        
        # Get all features
        all_features = self.get_all_features()
        
        # Filter features to only those in this project
        project_features = [f for f in all_features if f.get('project') == self.project_id]
        
        # Delete features that match configuration names
        print(f"\n1. Deleting feature flags from configuration.json...")
        deleted_count = 0
        for feature in project_features:
            feature_key = feature.get('id', '')  # In GrowthBook, 'id' is the feature key
            feature_id = feature.get('id', '')
            
            if feature_key in config_feature_names:
                if self.delete_feature(feature_id, feature_key):
                    deleted_count += 1
                # Rate limiting: Wait 1 second between deletions to avoid 429 errors
                time.sleep(1)
        
        print(f"\n  Deleted {deleted_count}/{len(config_feature_names)} features")
        
        # Delete saved groups created during migration
        print("\n2. Deleting saved groups...")
        all_groups = self.get_all_saved_groups()
        
        # Filter to only groups in this project
        project_groups = [g for g in all_groups if self.project_id in g.get('projects', [])]
        
        deleted_group_count = 0
        for group in project_groups:
            group_name = group.get('name', '')  # Changed from 'groupName' to 'name'
            group_id = group.get('id', '')
            
            # Delete groups that match migration patterns
            # Groups created for user types and segments
            migration_prefixes = [
                'user_', 'segment_', 'country_', 'os_', 'language_',
                'currency_', 'flavor_', 'utm_', 'ab_', 'cohort_'
            ]
            
            if any(group_name.startswith(prefix) for prefix in migration_prefixes):
                if self.delete_saved_group(group_id, group_name):
                    deleted_group_count += 1
                # Rate limiting: Wait 1 second between deletions to avoid 429 errors
                time.sleep(1)
        
        print(f"\n  Deleted {deleted_group_count} saved groups")
        
        # Delete attributes created during migration
        print("\n3. Deleting attributes...")
        all_attributes = self.get_all_attributes()
        
        # Common attributes from migration
        migrated_attributes = {
            # Standard attributes
            'os', 'os_version', 'country', 'country_group', 'language',
            'currency', 'flavor', 'utm_campaign', 'utm_source', 'utm_medium',
            'utm_content', 'utm_term', 'ab', 'cohort', 'browser',
            'pusher_app', 'forced_update', 'suggested_update',
            # Boolean user type attributes
            'is_beta', 'is_authenticated', 'is_verified', 'is_creator',
            'is_curator', 'is_banned', 'is_owner', 'is_nsfw_enabled',
            'is_partner', 'client_id'
        }
        
        deleted_attribute_count = 0
        for attribute in all_attributes:
            attribute_name = attribute.get('property', '')
            attribute_id = attribute.get('property', '')  # In GrowthBook, property is the ID
            
            # Only delete if it's in our known migrated attributes
            # and not a default GrowthBook attribute (id, deviceId, etc.)
            default_attributes = {
                'id', 'deviceId', 'company', 'loggedIn', 'employee', 'url', 
                'browser', 'path', 'host', 'query', 'deviceType'
            }
            
            if attribute_name in migrated_attributes and attribute_name not in default_attributes:
                if self.delete_attribute(attribute_id, attribute_name):
                    deleted_attribute_count += 1
                # Rate limiting: Wait 1 second between deletions to avoid 429 errors
                time.sleep(1)
        
        print(f"\n  Deleted {deleted_attribute_count} attributes")
        
        print("\n" + "="*60)
        print("REVERT COMPLETE")
        print("="*60)
        print(f"Features deleted: {deleted_count}")
        print(f"Saved groups deleted: {deleted_group_count}")
        print(f"Attributes deleted: {deleted_attribute_count}")


def main():
    # Configuration from environment variables
    API_URL = os.getenv('GROWTHBOOK_API_URL', 'http://localhost:3100/api/v1')
    API_KEY = os.getenv('GROWTHBOOK_API_KEY')
    PROJECT_ID = os.getenv('GROWTHBOOK_PROJECT')
    
    if not API_KEY:
        print("✗ GROWTHBOOK_API_KEY environment variable not set")
        return
    
    if not PROJECT_ID:
        print("✗ GROWTHBOOK_PROJECT environment variable not set")
        return
    
    print(f"GrowthBook API URL: {API_URL}")
    print(f"Project ID: {PROJECT_ID}")
    
    # Read configuration file to get feature names
    print("\nReading configuration.json to identify features to delete...")
    config_path = '/home/cuongbtq/scripts/configuration.json'
    
    if not os.path.exists(config_path):
        print(f"✗ Configuration file not found: {config_path}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    config_feature_names = set(config_data.keys())
    print(f"Found {len(config_feature_names)} features in configuration.json")
    
    # Confirm before proceeding
    print("\n" + "⚠"*30)
    print("WARNING: This will DELETE all features, saved groups, and attributes")
    print("created by the migration script!")
    print("⚠"*30)
    
    confirmation = input("\nType 'YES' to confirm deletion: ")
    if confirmation != 'YES':
        print("\n✗ Revert cancelled")
        return
    
    # Initialize reverter and run
    reverter = GrowthBookReverter(API_URL, API_KEY, PROJECT_ID)
    reverter.revert_migration(config_feature_names)


if __name__ == '__main__':
    main()
