#!/usr/bin/env python3
"""
Revert all changes made by migrate_to_unleash.py

This script will:
1. Delete all feature flags created from configuration.json
2. Delete all context fields created during migration
"""

import json
import requests
import os
from typing import Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a session for maintaining login
session = requests.Session()


def unleash_login(unleash_url: str, username: str, password: str):
    """Login to Unleash and create a session"""
    login_url = f"{unleash_url}/auth/simple/login"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = session.post(login_url, json=payload)
        if response.status_code in [200, 201, 302]:
            print("✓ Successfully logged in to Unleash")
            return True
        else:
            print(f"✗ Failed to login: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error logging in: {e}")
        return False


class UnleashReverter:
    def __init__(self, unleash_url: str, project: str = "default"):
        self.unleash_url = unleash_url.rstrip('/')
        self.project = project
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def get_all_features(self) -> list:
        """Get all features in the project."""
        try:
            response = session.get(
                f"{self.unleash_url}/api/admin/projects/{self.project}/features",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                print(f"Found {len(features)} features in project '{self.project}'")
                return features
            else:
                print(f"✗ Failed to get features: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Error getting features: {e}")
            return []
    
    def delete_feature(self, feature_name: str) -> bool:
        """Delete a feature flag."""
        try:
            # First, archive the feature
            archive_response = session.delete(
                f"{self.unleash_url}/api/admin/projects/{self.project}/features/{feature_name}",
                headers=self.headers
            )
            
            if archive_response.status_code not in [200, 202]:
                print(f"  ✗ Failed to archive feature {feature_name}: {archive_response.status_code}")
                return False
            
            # Then, permanently delete from archive
            delete_response = session.delete(
                f"{self.unleash_url}/api/admin/archive/{feature_name}",
                headers=self.headers
            )
            
            if delete_response.status_code in [200, 202]:
                print(f"  ✓ Deleted feature: {feature_name}")
                return True
            else:
                print(f"  ⚠ Archived but not deleted: {feature_name} (status: {delete_response.status_code})")
                return True  # Still consider it success if archived
        except Exception as e:
            print(f"  ✗ Error deleting feature {feature_name}: {e}")
            return False
    
    def get_all_segments(self) -> list:
        """Get all segments."""
        try:
            response = session.get(
                f"{self.unleash_url}/api/admin/segments",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                segments = data.get('segments', [])
                print(f"Found {len(segments)} segments")
                return segments
            else:
                print(f"✗ Failed to get segments: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Error getting segments: {e}")
            return []
    
    def delete_segment(self, segment_id: int, segment_name: str) -> bool:
        """Delete a segment."""
        try:
            response = session.delete(
                f"{self.unleash_url}/api/admin/segments/{segment_id}",
                headers=self.headers
            )
            if response.status_code in [200, 202, 204]:
                print(f"  ✓ Deleted segment: {segment_name} (ID: {segment_id})")
                return True
            else:
                print(f"  ✗ Failed to delete segment {segment_name}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error deleting segment {segment_name}: {e}")
            return False
    
    def get_all_context_fields(self) -> list:
        """Get all context fields."""
        try:
            response = session.get(
                f"{self.unleash_url}/api/admin/context",
                headers=self.headers
            )
            if response.status_code == 200:
                fields = response.json()
                print(f"Found {len(fields)} context fields")
                return fields
            else:
                print(f"✗ Failed to get context fields: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Error getting context fields: {e}")
            return []
    
    def delete_context_field(self, field_name: str) -> bool:
        """Delete a context field."""
        try:
            response = session.delete(
                f"{self.unleash_url}/api/admin/context/{field_name}",
                headers=self.headers
            )
            if response.status_code in [200, 202]:
                print(f"  ✓ Deleted context field: {field_name}")
                return True
            else:
                print(f"  ✗ Failed to delete context field {field_name}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error deleting context field {field_name}: {e}")
            return False
    
    def revert_migration(self, config_feature_names: Set[str]):
        """Revert the migration by deleting features, segments, and context fields."""
        print("\n" + "="*60)
        print("REVERTING UNLEASH MIGRATION")
        print("="*60)
        
        # Get all features
        all_features = self.get_all_features()
        
        # Delete features that match configuration names
        print(f"\n1. Deleting {len(config_feature_names)} feature flags...")
        deleted_count = 0
        for feature in all_features:
            feature_name = feature['name']
            if feature_name in config_feature_names:
                if self.delete_feature(feature_name):
                    deleted_count += 1
        
        print(f"\n  Deleted {deleted_count}/{len(config_feature_names)} features")
        
        # Delete segments created during migration
        print("\n2. Deleting segments...")
        all_segments = self.get_all_segments()
        
        deleted_segment_count = 0
        for segment in all_segments:
            segment_name = segment['name']
            segment_id = segment['id']
            
            # Delete segments that match migration patterns:
            # - user_* (user type segments)
            # - segment_* (operator-based segments)
            if segment_name.startswith('user_') or segment_name.startswith('segment_'):
                if self.delete_segment(segment_id, segment_name):
                    deleted_segment_count += 1
        
        print(f"\n  Deleted {deleted_segment_count} segments")
        
        # Get context fields created during migration
        print("\n3. Deleting context fields...")
        all_context_fields = self.get_all_context_fields()
        
        # Common context fields from migration
        migrated_context_fields = {
            # Standard context fields
            'os', 'os_version', 'country', 'country-group', 'language', 
            'currency', 'flavor', 'utm_campaign', 'utm_source', 'utm_medium',
            'utm_content', 'utm_term', 'ab', 'cohort', 'browser', 
            'pusher-app', 'forced-update', 'suggested-update',
            # Boolean user type fields
            'is_beta', 'is_authenticated', 'is_verified', 'is_creator',
            'is_curator', 'is_banned', 'is_owner'
        }
        
        deleted_context_count = 0
        for field in all_context_fields:
            field_name = field['name']
            # Only delete if it's in our known migrated fields
            # and not a default Unleash field
            if field_name in migrated_context_fields:
                if self.delete_context_field(field_name):
                    deleted_context_count += 1
        
        print(f"\n  Deleted {deleted_context_count} context fields")
        
        print("\n" + "="*60)
        print("REVERT COMPLETE")
        print("="*60)
        print(f"Features deleted: {deleted_count}")
        print(f"Segments deleted: {deleted_segment_count}")
        print(f"Context fields deleted: {deleted_context_count}")


def main():
    # Configuration from environment variables
    UNLEASH_URL = os.getenv('UNLEASH_URL', 'http://localhost:4242')
    PROJECT = os.getenv('UNLEASH_PROJECT', 'default')
    USERNAME = os.getenv('UNLEASH_USERNAME', 'admin')
    PASSWORD = os.getenv('UNLEASH_PASSWORD', 'unleash4all')
    
    print(f"Unleash URL: {UNLEASH_URL}")
    print(f"Project: {PROJECT}")
    print(f"Username: {USERNAME}")
    
    # Login to Unleash
    print("\nLogging in to Unleash...")
    if not unleash_login(UNLEASH_URL, USERNAME, PASSWORD):
        print("\n✗ Cannot proceed without authentication")
        return
    
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
    print("WARNING: This will DELETE all features, segments, and context fields")
    print("created by the migration script!")
    print("⚠"*30)
    
    confirmation = input("\nType 'YES' to confirm deletion: ")
    if confirmation != 'YES':
        print("\n✗ Revert cancelled")
        return
    
    # Initialize reverter and run
    reverter = UnleashReverter(UNLEASH_URL, PROJECT)
    reverter.revert_migration(config_feature_names)


if __name__ == '__main__':
    main()
