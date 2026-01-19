#!/usr/bin/env python3
"""
Migrate configuration.json to Unleash Feature Flags.

Architecture:
- First layer = Feature Flag name
- Second layer:
  - default key = Default variant (fallback)
  - User type keys (beta, creator, etc.) = Boolean context fields + segments
  - nsfw key = Multi-condition variant (browser OR creator OR utm_term)
  - Operator keys (os, country, etc.) = Segments for specific keys, constraints for others
"""

import json
import requests
import os
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a session for maintaining login
session = requests.Session()

# Context fields that should use segments instead of inline constraints
SEGMENT_ENABLED_CONTEXTS = {
    'os', 'os_version', 'country', 'country-group', 'language', 
    'currency', 'flavor', 'browser', 'pusher-app', 'forced-update', 
    'suggested-update', 'cohort', 'ab'
}

# UTM parameters should also use segments
UTM_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'}
SEGMENT_ENABLED_CONTEXTS.update(UTM_PARAMS)


def unleash_login(unleash_url: str, username: str, password: str) -> bool:
    """Login to Unleash and create a session"""
    login_url = f"{unleash_url}/auth/simple/login"
    payload = {"username": username, "password": password}
    
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


def unleash_logout(unleash_url: str) -> bool:
    """Logout from Unleash and close the session"""
    logout_url = f"{unleash_url}/auth/simple/logout"
    
    try:
        response = session.post(logout_url)
        session.close()
        print("✓ Successfully logged out and closed session")
        return True
    except Exception as e:
        print(f"✗ Error during logout: {e}")
        session.close()  # Close session anyway
        return False


class UnleashMigrator:
    """Migrates configuration to Unleash Feature Flags with segment management."""
    
    def __init__(self, unleash_url: str, project: str = "default", environment: str = "development"):
        self.unleash_url = unleash_url.rstrip('/')
        self.project = project
        self.environment = environment
        self.headers = {'Content-Type': 'application/json'}
        
        # Tracking
        self.existing_context_fields = set()
        self.existing_segments = {}  # segment name -> segment id
        
        # Load existing resources
        self._load_existing_context_fields()
        self._load_existing_segments()
    
    def _load_existing_context_fields(self):
        """Load existing context fields from Unleash."""
        try:
            response = session.get(f"{self.unleash_url}/api/admin/context", headers=self.headers)
            if response.status_code == 200:
                for field in response.json():
                    self.existing_context_fields.add(field['name'])
            print(f"Loaded {len(self.existing_context_fields)} existing context fields")
        except Exception as e:
            print(f"Warning: Could not load context fields: {e}")
    
    def _load_existing_segments(self):
        """Load existing segments from Unleash."""
        try:
            response = session.get(f"{self.unleash_url}/api/admin/segments", headers=self.headers)
            if response.status_code == 200:
                segments = response.json().get('segments', [])
                for segment in segments:
                    segment_name = segment['name']
                    segment_id = segment['id']
                    self.existing_segments[segment_name] = segment_id
                        
            print(f"Loaded {len(self.existing_segments)} existing segments")
        except Exception as e:
            print(f"Warning: Could not load segments: {e}")
    
    def create_context_field(self, field_name: str, description: str = "") -> bool:
        """Create context field if it doesn't exist."""
        if field_name in self.existing_context_fields:
            return True
        
        payload = {
            "name": field_name,
            "description": description or f"Auto-generated context field for {field_name}",
            "legalValues": [],
            "stickiness": False
        }
        
        try:
            response = session.post(
                f"{self.unleash_url}/api/admin/context",
                headers=self.headers,
                json=payload
            )
            if response.status_code in [200, 201]:
                self.existing_context_fields.add(field_name)
                print(f"  ✓ Created context field: {field_name}")
                return True
            else:
                print(f"  ✗ Failed to create context field {field_name}: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ Error creating context field {field_name}: {e}")
            return False
    
    def create_segment(self, segment_name: str, description: str, constraints: List[Dict]) -> Optional[int]:
        """Create a segment if it doesn't exist."""
        # Check if segment already exists
        if segment_name in self.existing_segments:
            return self.existing_segments[segment_name]
        
        payload = {
            "name": segment_name,
            "description": description,
            "constraints": constraints
        }
        
        try:
            response = session.post(
                f"{self.unleash_url}/api/admin/segments",
                headers=self.headers,
                json=payload
            )
            if response.status_code in [200, 201]:
                segment_data = response.json()
                segment_id = segment_data.get('id')
                self.existing_segments[segment_name] = segment_id
                print(f"    ✓ Created segment: {segment_name} (ID: {segment_id})")
                return segment_id
            else:
                print(f"    ✗ Failed to create segment: {response.status_code}")
                return None
        except Exception as e:
            print(f"    ✗ Error creating segment: {e}")
            return None
    
    def create_feature_flag(self, feature_name: str) -> bool:
        """Create a feature flag if it doesn't exist."""
        # Check if feature exists
        try:
            response = session.get(
                f"{self.unleash_url}/api/admin/projects/{self.project}/features/{feature_name}",
                headers=self.headers
            )
            if response.status_code == 200:
                return True
        except:
            pass
        
        # Create new feature
        payload = {
            "name": feature_name,
            "description": f"Migrated configuration for {feature_name}",
            "type": "release",
            "impressionData": False
        }
        
        try:
            response = session.post(
                f"{self.unleash_url}/api/admin/projects/{self.project}/features",
                headers=self.headers,
                json=payload
            )
            if response.status_code in [200, 201]:
                print(f"✓ Created feature flag: {feature_name}")
                return True
            else:
                print(f"✗ Failed to create feature flag: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error creating feature flag: {e}")
            return False
    
    def set_default_variant(self, feature_name: str, variant_value: Any) -> bool:
        """Set default variant for a feature (fallback when no strategies match)."""
        # Prepare variant payload
        if isinstance(variant_value, list):
            payload_data = json.dumps(variant_value)
        else:
            payload_data = str(variant_value)
        
        variant = {
            "name": "default",
            "weight": 1000,
            "weightType": "variable",
            "stickiness": "default",
            "payload": {
                "type": "json",
                "value": payload_data
            }
        }
        
        # Create a strategy without constraints (always matches)
        strategy_data = {
            "name": "flexibleRollout",
            "constraints": [],
            "segments": [],
            "parameters": {
                "rollout": "100",
                "stickiness": "default",
                "groupId": feature_name
            },
            "variants": [variant]
        }
        
        try:
            strategy_url = f"{self.unleash_url}/api/admin/projects/{self.project}/features/{feature_name}/environments/{self.environment}/strategies"
            response = session.post(strategy_url, headers=self.headers, json=strategy_data)
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Set default variant")
                return True
            else:
                print(f"  ✗ Failed to set default variant: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ Error setting default variant: {e}")
            return False
    
    def add_variant_with_condition(self, feature_name: str, variant_name: str, 
                                   variant_value: Any, segment_ids: List[int] = None, 
                                   constraints: List[Dict] = None) -> bool:
        """Add a variant with segments or constraints."""
        # Prepare variant payload
        if isinstance(variant_value, list):
            payload_data = json.dumps(variant_value)
        else:
            payload_data = str(variant_value)
        
        variant = {
            "name": variant_name,
            "weight": 1000,
            "weightType": "variable",
            "stickiness": "default",
            "payload": {
                "type": "json",
                "value": payload_data
            }
        }
        
        # Create strategy with variant
        strategy_data = {
            "name": "flexibleRollout",
            "constraints": constraints or [],
            "segments": segment_ids or [],
            "parameters": {
                "rollout": "100",
                "stickiness": "default",
                "groupId": feature_name
            },
            "variants": [variant]
        }
        
        try:
            strategy_url = f"{self.unleash_url}/api/admin/projects/{self.project}/features/{feature_name}/environments/{self.environment}/strategies"
            response = session.post(strategy_url, headers=self.headers, json=strategy_data)
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Added variant: {variant_name}")
                return True
            else:
                print(f"  ✗ Failed to add variant: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error adding variant: {e}")
            return False
    
    def process_default_key(self, feature_name: str, value: Any):
        """Process default key - set as fallback variant."""
        print(f"  → Default variant (fallback)")
        self.set_default_variant(feature_name, value)
    
    def process_user_type_key(self, feature_name: str, key: str, value: Any):
        """Process user type keys - create boolean context field and segment."""
        print(f"  → User type: {key}")
        
        # Create boolean context field: is_beta, is_creator, etc.
        context_field_name = f"is_{key}"
        self.create_context_field(context_field_name, f"Boolean flag: is user {key}")
        
        # Create segment with constraint: is_beta == true
        segment_name = f"user_{key}"
        constraint = {
            "contextName": context_field_name,
            "operator": "IN",
            "values": ["true"]
        }
        
        segment_id = self.create_segment(segment_name, f"Users with {key} status", [constraint])
        
        if segment_id:
            print(f"    → Using segment: {segment_name}")
            self.add_variant_with_condition(feature_name, key, value, segment_ids=[segment_id])
        else:
            print(f"    → Fallback to inline constraint")
            self.add_variant_with_condition(feature_name, key, value, constraints=[constraint])
    
    def process_nsfw_key(self, feature_name: str, value: Any):
        """Process nsfw key - create multiple OR strategies."""
        print(f"  → NSFW variant (multi-condition OR)")
        
        # Ensure context fields exist
        self.create_context_field('browser', 'Context field for browser type')
        self.create_context_field('is_creator', 'Boolean flag: is user creator')
        self.create_context_field('utm_term', 'Context field for UTM term tracking')
        
        # Strategy 1: browser == web
        print(f"    → Condition 1: browser == web")
        segment_name_browser = "segment_browser_web"
        constraint_browser = {
            "contextName": "browser",
            "operator": "IN",
            "values": ["web"]
        }
        segment_id_browser = self.create_segment(segment_name_browser, "Web browser", [constraint_browser])
        
        if segment_id_browser:
            self.add_variant_with_condition(feature_name, "nsfw_browser_web", value, segment_ids=[segment_id_browser])
        else:
            self.add_variant_with_condition(feature_name, "nsfw_browser_web", value, constraints=[constraint_browser])
        
        # Strategy 2: is_creator == true
        print(f"    → Condition 2: user is creator")
        segment_name_creator = "user_creator"
        constraint_creator = {
            "contextName": "is_creator",
            "operator": "IN",
            "values": ["true"]
        }
        segment_id_creator = self.create_segment(segment_name_creator, "Creator users", [constraint_creator])
        
        if segment_id_creator:
            self.add_variant_with_condition(feature_name, "nsfw_creator", value, segment_ids=[segment_id_creator])
        else:
            self.add_variant_with_condition(feature_name, "nsfw_creator", value, constraints=[constraint_creator])
        
        # Strategy 3: utm_term in NSFW_ENABLED_UTM_TERMS
        print(f"    → Condition 3: utm_term (requires NSFW_ENABLED_UTM_TERMS config)")
    
    def process_operator_key(self, feature_name: str, key: str, values_dict: Dict[str, Any]):
        """Process operator-based keys - use segments for specific contexts, constraints for others."""
        print(f"  → Operator-based key: {key}")
        
        # Step 1: Create context field
        self.create_context_field(key, f"Context field for {key} matching")
        
        # Check if this context should use segments
        use_segments = key in SEGMENT_ENABLED_CONTEXTS
        
        if use_segments:
            print(f"    → Will use segments for '{key}' (in predefined list)")
        else:
            print(f"    → Will use inline constraints for '{key}' (not in segment list)")
        
        # Step 2 & 3: For each value, create segment or constraint and add variant
        for operator_value, config_value in values_dict.items():
            print(f"    → Value: {operator_value}")
            
            # Build constraint
            constraint = {
                "contextName": key,
                "operator": "IN",
                "values": [operator_value]
            }
            
            if use_segments:
                # Create segment for this value
                segment_name = f"segment_{key}_{operator_value}".replace('.', '_').replace('-', '_')
                segment_id = self.create_segment(segment_name, f"{key} = {operator_value}", [constraint])
                
                if segment_id:
                    print(f"      → Using segment")
                    variant_name = f"{key}_{operator_value}"
                    self.add_variant_with_condition(feature_name, variant_name, config_value, segment_ids=[segment_id])
                else:
                    print(f"      → Segment creation failed, using inline constraint")
                    variant_name = f"{key}_{operator_value}"
                    self.add_variant_with_condition(feature_name, variant_name, config_value, constraints=[constraint])
            else:
                # Use inline constraint
                print(f"      → Using inline constraint")
                variant_name = f"{key}_{operator_value}"
                self.add_variant_with_condition(feature_name, variant_name, config_value, constraints=[constraint])
    
    def process_configuration(self, config_data: Dict[str, Any], limit: int = None):
        """Process configuration and migrate to Unleash."""
        processed_count = 0
        total_count = len(config_data)
        
        for feature_name, config_block in config_data.items():
            if limit and processed_count >= limit:
                print(f"\n✓ Processed {limit} features (limit reached)")
                break
            
            processed_count += 1
            print(f"\n[{processed_count}/{total_count}] Processing feature: {feature_name}")
            
            # Create feature flag
            if not self.create_feature_flag(feature_name):
                print(f"  Skipping {feature_name} due to creation failure")
                continue
            
            if not isinstance(config_block, dict):
                print(f"  Warning: Config block is not a dictionary, skipping")
                continue
            
            # Process each second layer key
            for key, value in config_block.items():
                # Default key - fallback variant
                if key == 'default':
                    self.process_default_key(feature_name, value)
                
                # User type keys - create boolean context fields + segments
                elif key in ['beta', 'authenticated', 'verified', 'creator', 'curator', 'banned', 'owner']:
                    self.process_user_type_key(feature_name, key, value)
                
                # NSFW key - multi-condition OR
                elif key == 'nsfw':
                    self.process_nsfw_key(feature_name, value)
                
                # Operator-based keys - nested objects
                elif isinstance(value, dict):
                    self.process_operator_key(feature_name, key, value)
                
                # Unknown key type
                else:
                    print(f"  → Unknown key type: {key}, setting as default variant")
                    self.set_default_variant(feature_name, value)


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
    
    try:
        # Read configuration file
        print("\nReading configuration.json...")
        with open('/home/cuongbtq/scripts/configuration.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print(f"Loaded {len(config_data)} configuration items")
        
        # Initialize migrator
        migrator = UnleashMigrator(UNLEASH_URL, PROJECT)
        
        # Process configurations (limit to 20 for testing)
        migrator.process_configuration(config_data, limit=20)
        
        print("\n" + "="*60)
        print("Migration complete!")
        print("="*60)
    
    finally:
        # Always close the session
        print("\nClosing Unleash session...")
        unleash_logout(UNLEASH_URL)


if __name__ == '__main__':
    main()
