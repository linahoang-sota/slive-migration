import requests
import json
import os

class GrowthBook:
    def __init__(self, api_key, api_url="http://localhost:3100/api/v1", project="prj_4dxcy1nmkjg32kk", owner="nam.nguyen@sotatek.com"):
        """
        Initialize the GrowthBook client.

        Args:
            api_key (str): The GrowthBook API secret key.
            api_url (str, optional): The base URL for the API. Defaults to "http://localhost:3100/api/v1".
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        # attributes_cache will store a dict mapping property name to attribute data
        self.attributes_cache = {} 
        self._is_cache_loaded = False
        # saved_groups_cache will store saved groups by both name and id
        self.saved_groups_cache = {}  # {name: group_data, id: group_data}
        self._is_saved_groups_cache_loaded = False
        self.project = project
        self.owner = owner

    def _get_headers(self):
        """Returns the headers for API requests."""
        # Authenticate using Basic Auth with the API key as the username
        return {}

    def _get_auth(self):
         # basic auth with api_key as username and empty password
        return (self.api_key, "")

    def list_attributes(self, force_refresh=False):
        """
        Lists all attributes from GrowthBook and updates the local cache.

        Args:
            force_refresh (bool): If True, forces a fetch from the API even if cache is loaded.

        Returns:
            dict: A dictionary of attributes keyed by their property name.
        """
        if self._is_cache_loaded and not force_refresh:
            return self.attributes_cache

        url = f"{self.api_url}/attributes"
        try:
            response = requests.get(url, auth=self._get_auth())
            response.raise_for_status()
            data = response.json()
            
            # The API returns a list of attributes. 
            # Depending on the exact response structure (listing vs single), 
            # typically it's { "attributes": [...] } or just [...]
            # Based on docs usually: { "attributes": [...], "limit": ..., "offset": ... }
            # but curl example suggests direct access. 
            # We will assume standard paginated response or list.
            # Let's handle generic response.
            
            items = data.get("attributes", []) if isinstance(data, dict) else data

            # Update cache: map property -> attribute object
            self.attributes_cache = {item.get("property"): item for item in items}
            self._is_cache_loaded = True
            
            return self.attributes_cache
            
        except requests.exceptions.RequestException as e:
            print(f"Error listing attributes: {e}")
            return self.attributes_cache # Return existing cache on failure

    def create_attribute(self, property_key, datatype="string", description=None, tags=None):
        """
        Creates a new attribute in GrowthBook.

        Args:
            property_key (str): The name/key of the attribute (e.g., "user_id").
            datatype (str): The type of the attribute ("boolean", "number", "string", "array", "enum").
            description (str, optional): Description of the attribute.
            tags (list, optional): List of tags.

        Returns:
            dict: The created attribute data, or None if failed.
        """
        url = f"{self.api_url}/attributes"
        payload = {
            "property": property_key,
            "datatype": datatype
        }
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags

        try:
            response = requests.post(url, json=payload, auth=self._get_auth())
            response.raise_for_status()
            new_attr = response.json()
            
            # Usually the API returns the created object.
            # Sometimes it might be wrapped in {"attribute": ...}
            created_attr = new_attr.get("attribute", new_attr)
            
            # Update cache immediately
            self.attributes_cache[property_key] = created_attr
            
            print(f"Successfully created attribute: {property_key}")
            return created_attr
            
        except requests.exceptions.RequestException as e:
            print(f"Error creating attribute '{property_key}': {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def ensure_attribute(self, property_key, datatype="string", description="Migration from configuration.yaml"):
        """
        Checks if an attribute exists in the cache. If not, creates it.
        
        Args:
            property_key (str): The attribute key to check/ensure.
            datatype (str): The datatype to use if creation is needed.
            description (str): The description to use if creation is needed.
            
        Returns:
            dict: The existing or newly created attribute object.
        """
        # Ensure cache is populated at least once
        if not self._is_cache_loaded:
            self.list_attributes()

        if property_key in self.attributes_cache:
            return self.attributes_cache[property_key]
        
        # If not found, create it
        print(f"Attribute '{property_key}' not found in cache. Creating...")
        return self.create_attribute(property_key, datatype=datatype, description=description)

    def process_config_to_rules(self, config_value, config_key=None, except_file="except.json"):
        """
        Process configuration value from configuration.yaml and convert to GrowthBook rules format.
        Uses saved groups instead of inline conditions for better reusability.
        
        Handles multiple key conventions:
        1. 'default' - The default value
        2. Simple keys (beta, creator, authenticated, etc.) -> creates saved group with {is_<key>: true}
        3. Key=value pairs (country=cn) -> creates saved group with {country: cn}
        4. Ampersand-separated (utm_campaign=x&utm_medium=y) -> creates saved group with multiple conditions
        
        Skips and logs to except.json:
        - Hyphen-separated conditions (-)
        - Semicolon-separated conditions (;)
        
        Args:
            config_value (dict): Configuration value containing child keys like:
                {
                    'default': ['value1'],
                    'beta': ['value2'],
                    'creator': ['value3'],
                    'country=cn': ['value4'],
                    'utm_campaign=x&utm_medium=y': ['value5']
                }
            config_key (str, optional): The parent config key for logging purposes
            except_file (str, optional): Path to exception log file
        
        Returns:
            tuple: (default_value, rules_list, value_type, attributes_needed, skipped_keys)
                - default_value: The value from the 'default' key
                - rules_list: List of rule dictionaries for create_feature (using savedGroupTargeting)
                - value_type: Inferred value type ('string', 'number', 'boolean', 'json')
                - attributes_needed: Set of attribute names that need to be created
                - skipped_keys: List of keys that were skipped
        """
        if not isinstance(config_value, dict):
            print(f"Warning: config_value is not a dictionary")
            return None, [], "string", set(), []
        
        # Simple keys that should be converted to is_<key>=true
        SIMPLE_KEYS = {
            'beta', 'authenticated', 'verified', 'creator', 'curator', 
            'banned', 'nsfw', 'owner'
        }
        
        default_value = None
        rules = []
        value_type = "string"
        attributes_needed = set()
        skipped_keys = []
        
        # Process each child key
        for child_key, child_value in config_value.items():
            # Extract the actual value (handle list or direct value)
            actual_value = self._extract_value(child_value)
            
            # Handle 'default' key
            if child_key == "default":
                default_value = actual_value
                # Infer value type from default value
                value_type = self._infer_value_type(actual_value)
                continue
            
            # Check for unsupported separators (hyphen or semicolon)
            if self._has_unsupported_separator(child_key):
                # Determine which separator type it is
                separator_type = "semicolon" if ";" in child_key else "hyphen"
                print(f"⚠ Skipping {child_key}: contains unsupported separator ({separator_type})")
                skipped_keys.append({
                    "config_key": config_key,
                    "child_key": child_key,
                    "reason": f"unsupported_separator_{separator_type}",
                    "value": actual_value
                })
                continue

            
            # Handle simple keys (beta, creator, etc.)
            if child_key in SIMPLE_KEYS:
                attribute_name = f"is_{child_key}"
                attributes_needed.add(attribute_name)
                
                # Create saved group for this condition
                group_name = child_key
                condition = {attribute_name: "true"}
                group_id = self.ensure_saved_group(name=group_name, condition=condition)
                
                rule = {
                    "value": actual_value,
                    "description": f"{child_key} users",
                    "enabled": True,
                    "savedGroupTargeting": [{"matchType": "all", "savedGroups": [group_id]}]
                }
                rules.append(rule)
                continue
            
            # Handle ampersand-separated conditions (utm_campaign=x&utm_medium=y)
            if "&" in child_key:
                condition_dict, attrs = self._parse_ampersand_conditions(child_key)
                attributes_needed.update(attrs)
                
                # Create saved group for this condition
                group_name = child_key
                group_id = self.ensure_saved_group(name=group_name, condition=condition_dict)
                
                rule = {
                    "value": actual_value,
                    "description": child_key,
                    "enabled": True,
                    "savedGroupTargeting": [{"matchType": "all", "savedGroups": [group_id]}]
                }
                rules.append(rule)
                continue
            
            # Handle standard key=value pairs
            if "=" in child_key:
                parts = child_key.split("=", 1)  # Split only on first "="
                attribute_name = parts[0]
                condition_value = parts[1] if len(parts) > 1 else ""
                
                attributes_needed.add(attribute_name)
                
                # Create saved group for this condition
                group_name = child_key
                condition = {attribute_name: condition_value}
                group_id = self.ensure_saved_group(name=group_name, condition=condition)
                
                rule = {
                    "value": actual_value,
                    "description": f"{attribute_name}={condition_value}",
                    "enabled": True,
                    "savedGroupTargeting": [{"matchType": "all", "savedGroups": [group_id]}]
                }
                rules.append(rule)
                continue
            
            # Skip unrecognized patterns
            print(f"⚠ Skipping {child_key}: unrecognized pattern")
            skipped_keys.append({
                "config_key": config_key,
                "child_key": child_key,
                "reason": "unrecognized_pattern",
                "value": actual_value
            })
        
        # Log skipped keys to except.json if any
        if skipped_keys:
            self._log_exceptions(skipped_keys, except_file)
        
        # If no default value was found, use empty string
        if default_value is None:
            default_value = ""
            print("Warning: No 'default' key found in config_value, using empty string")
        
        return default_value, rules, value_type, attributes_needed, skipped_keys
    
    def _has_unsupported_separator(self, key):
        """
        Check if a key contains unsupported separators (hyphen or semicolon).
        
        Supported patterns:
        - key=value (simple)
        - key1=value1&key2=value2 (ampersand-separated, supported)
        
        Unsupported patterns:
        - key1=value1;key2=value2 (semicolon-separated)
        - key1=value1-key2=value2 (hyphen-separated, NOT ampersand)
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if contains unsupported separator
        """
        # If no '=' in key, it's not a condition pattern
        if "=" not in key:
            return False
        
        # First, check if it's an ampersand-separated pattern (supported)
        # If so, we should NOT flag hyphens within the values
        if "&" in key:
            # This is ampersand-separated, which is supported
            # Hyphens within values are allowed (e.g., utm_medium=non-rtb)
            # But we still need to check for semicolons
            value_part = key.split("=", 1)[1]
            if ";" in value_part and "=" in value_part:
                # Semicolon used as separator (unsupported)
                return True
            # Ampersand pattern is supported, don't flag hyphens
            return False
        
        # Not ampersand-separated, check for other separators
        value_part = key.split("=", 1)[1]
        
        # Check for semicolon separator
        if ";" in value_part:
            # Check if semicolon is used as a separator (has another key=value after it)
            # Split by semicolon and check if multiple parts have '='
            parts = value_part.split(";")
            parts_with_equals = sum(1 for part in parts if "=" in part)
            if parts_with_equals > 0:
                # Semicolon is being used as a separator
                return True
        
        # Check for hyphen separator (only if NOT in ampersand pattern)
        if "-" in value_part:
            # Check if hyphen is used as a separator (has another key=value after it)
            # Split by hyphen and check if multiple parts have '='
            parts = value_part.split("-")
            parts_with_equals = sum(1 for part in parts if "=" in part)
            if parts_with_equals > 0:
                # Hyphen is being used as a separator
                return True
        
        return False

    
    def _log_exceptions(self, exceptions, except_file):
        """
        Log exceptions to a JSON file.
        
        Args:
            exceptions: List of exception dictionaries
            except_file: Path to the exception log file
        """
        # Load existing exceptions if file exists
        existing_exceptions = []
        if os.path.exists(except_file):
            try:
                with open(except_file, 'r', encoding='utf-8') as f:
                    existing_exceptions = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse existing {except_file}, will overwrite")
        
        # Append new exceptions
        existing_exceptions.extend(exceptions)
        
        # Write back to file
        with open(except_file, 'w', encoding='utf-8') as f:
            json.dump(existing_exceptions, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Logged {len(exceptions)} skipped keys to {except_file}")

    
    def _extract_value(self, child_value):
        """Extract actual value from potentially nested list structure."""
        actual_value = child_value
        if isinstance(child_value, list):
            if len(child_value) == 1:
                actual_value = child_value[0]
            elif len(child_value) == 0:
                actual_value = ""
            # For multiple elements, keep the list structure
        return actual_value
    
    def _parse_ampersand_conditions(self, condition_string):
        """
        Parse ampersand-separated conditions into a condition dictionary.
        
        Args:
            condition_string: e.g., "utm_campaign=my_routine&utm_medium=non-rtb&utm_source=cheongdb2u"
            
        Returns:
            tuple: (condition_dict, attributes_set)
                - condition_dict: e.g., {"utm_campaign": "my_routine", "utm_medium": "non-rtb", ...}
                - attributes_set: Set of attribute names
        """
        condition_dict = {}
        attributes_set = set()
        
        # Split by '&' to get individual conditions
        parts = condition_string.split("&")
        
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                condition_dict[key] = value
                attributes_set.add(key)
            else:
                print(f"Warning: Invalid condition part '{part}' in '{condition_string}'")
        
        return condition_dict, attributes_set
    
    def _infer_value_type(self, value):
        """
        Infer GrowthBook value type from a Python value.
        
        Args:
            value: The value to infer type from
            
        Returns:
            str: One of 'boolean', 'number', 'string', 'json'
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, (list, dict)):
            return "json"
        else:
            return "string"

    def create_feature(self, feature_id, value_type, default_value, description="", rules=None, environment="production"):
        """
        Creates a feature flag in GrowthBook.
        
        Args:
            feature_id (str): The unique identifier for the feature (config_key).
            value_type (str): The type of the feature value ("boolean", "string", "number", "json").
            default_value: The default value for the feature.
            description (str, optional): Description of the feature.
            rules (list, optional): List of rule dictionaries. Each rule should have:
                - condition (dict): Dictionary mapping attribute_name to condition value
                - value: The value to return when condition matches
                - description (str, optional): Rule description
                - enabled (bool, optional): Whether the rule is enabled (default: True)
            environment (str, optional): The environment to create the feature in (default: "production").
            
        Returns:
            dict: The created or updated feature data, or None if failed.
            
        Example:
            rules = [
                {
                    "condition": {"country": "cn"},
                    "value": "https://sst011.fyfys.cn/battlepass/main/index.html",
                    "description": "China URL"
                },
                {
                    "condition": {"country": "my"},
                    "value": "https://public.sophisticatedwondersasiangems.xyz/battlepass/main/index.html",
                    "description": "Malaysia URL"
                }
            ]
            gb.create_feature("USER_EVENT_REPORT_URL", "string", "https://swag.live/battlepass/index.html", rules=rules)
        """
        # Check if feature already exists
        existing_feature = self.get_feature(feature_id)
        
        # Build the rules array for the environment
        formatted_rules = []
        if rules:
            for rule in rules:
                # Convert condition dict to JSON string format
                condition_dict = rule.get("condition", {})
                condition_json = json.dumps(condition_dict)
                
                formatted_rule = {
                    "description": rule.get("description", ""),
                    "condition": condition_json,
                    "enabled": rule.get("enabled", True),
                    "type": "force",
                    "value": json.dumps(rule.get("value")) if value_type == "json" else str(rule.get("value", ""))
                }
                
                # Add savedGroupTargeting if provided
                if "savedGroupTargeting" in rule:
                    formatted_rule["savedGroupTargeting"] = rule["savedGroupTargeting"]
                
                formatted_rules.append(formatted_rule)
        
        # Build the payload
        payload = {
            "description": description,
            "defaultValue": json.dumps(default_value) if value_type == "json" else str(default_value),
            "owner": self.owner,
            "project": self.project, 
            "environments": {
                environment: {
                    "enabled": True,
                    "rules": list(reversed(formatted_rules))
                }
            }
        }

        if existing_feature:
            print(f"Feature '{feature_id}' already exists. Updating...")
            return self.update_feature(feature_id, payload)
        
        # If not exists, add ID to payload and create
        payload["id"] = feature_id
        payload["valueType"] = value_type
        url = f"{self.api_url}/features"
        
        try:
            response = requests.post(url, json=payload, auth=self._get_auth())
            response.raise_for_status()
            created_feature = response.json()
            
            print(f"✓ Successfully created feature: {feature_id}")
            print("feature payload: ", json.dumps(payload))
            return created_feature
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating feature '{feature_id}': {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def get_feature(self, feature_id):
        """
        Get a single feature by ID.
        
        Args:
            feature_id (str): The feature key.
            
        Returns:
            dict: The feature object if found, None otherwise.
        """
        url = f"{self.api_url}/features/{feature_id}"
        try:
            response = requests.get(url, auth=self._get_auth())
            if response.status_code == 400:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Check if it's a 404 which means not found (handled above actually, but for other errors)
            if e.response is not None and e.response.status_code == 404:
                return None
            print(f"Error getting feature '{feature_id}': {e}")
            return None

    def update_feature(self, feature_id, payload):
        """
        Update an existing feature using PUT.
        
        Args:
            feature_id (str): The feature key.
            payload (dict): The payload to update.
            
        Returns:
            dict: The updated feature object, or None if failed.
        """
        url = f"{self.api_url}/features/{feature_id}"
        try:
            response = requests.post(url, json=payload, auth=self._get_auth())
            response.raise_for_status()
            updated_feature = response.json()
            print(f"✓ Successfully updated feature: {feature_id}")
            return updated_feature
        except requests.exceptions.RequestException as e:
            print(f"✗ Error updating feature '{feature_id}': {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def list_saved_groups(self, force_refresh=False):
        """
        Lists all saved groups from GrowthBook and updates the local cache.
        
        Args:
            force_refresh (bool): If True, forces a fetch from the API even if cache is loaded.
            
        Returns:
            dict: A dictionary of saved groups keyed by both their name and id.
        """
        if self._is_saved_groups_cache_loaded and not force_refresh:
            return self.saved_groups_cache
        
        url = f"{self.api_url}/saved-groups"
        try:
            response = requests.get(url, auth=self._get_auth())
            response.raise_for_status()
            data = response.json()
            
            # The API returns a list of saved groups
            # Response structure: {"savedGroups": [...], "limit": ..., "offset": ...}
            items = data.get("savedGroups", []) if isinstance(data, dict) else data
            
            # Update cache: map both name and id -> saved group object
            self.saved_groups_cache = {}
            for item in items:
                group_name = item.get("groupName") or item.get("name")
                group_id = item.get("id")
                if group_name:
                    self.saved_groups_cache[group_name] = item
                if group_id:
                    self.saved_groups_cache[group_id] = item
            
            self._is_saved_groups_cache_loaded = True
            
            return self.saved_groups_cache
            
        except requests.exceptions.RequestException as e:
            print(f"Error listing saved groups: {e}")
            return self.saved_groups_cache  # Return existing cache on failure

    def get_saved_group(self, group_id):
        """
        Get a saved group by ID.
        
        Args:
            group_id (str): The ID of the saved group.
            
        Returns:
            dict: The saved group object, or None if not found.
        """
        url = f"{self.api_url}/saved-groups/{group_id}"
        try:
            response = requests.get(url, auth=self._get_auth())
            if response.status_code == 400:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            print(f"Error getting saved group '{group_id}': {e}")
            return None

    def create_saved_group(self, name, condition, projects=None):
        """
        Create a new saved group.
        
        Args:
            name (str): The display name for the group.
            condition (dict or str): The condition logic (same as rules).
            description (str, optional): Description of the group.
            projects (list, optional): List of project IDs. Defaults to [self.project].
            
        Returns:
            str: The ID of the created saved group, or None if failed.
        """
        url = f"{self.api_url}/saved-groups"
        
        if projects is None and self.project:
            projects = [self.project]
        elif projects is None:
            projects = []
            
        if isinstance(condition, dict):
            condition_str = json.dumps(condition)
        else:
            condition_str = str(condition)

        payload = {
            "type": "condition",
            "name": name,
            "owner": self.owner,
            "condition": condition_str,
            "projects": projects
        }
        
        try:
            response = requests.post(url, json=payload, auth=self._get_auth())
            response.raise_for_status()
            created_group = response.json()
            
            # Update cache with the newly created group
            group_data = created_group.get("savedGroup", created_group)
            group_name = group_data.get("groupName") or group_data.get("name")
            group_id = group_data.get("id")
            
            if group_name:
                self.saved_groups_cache[group_name] = group_data
            if group_id:
                self.saved_groups_cache[group_id] = group_data
            
            print(f"✓ Successfully created saved group: {name} (ID: {group_id})")
            return group_id
        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating saved group '{name}': {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def update_saved_group(self, group_id, payload):
        """
        Update an existing saved group.
        
        Args:
            group_id (str): The ID of the saved group.
            payload (dict): The payload to update.
            
        Returns:
            str: The ID of the updated saved group, or None if failed.
        """
        url = f"{self.api_url}/saved-groups/{group_id}"
        try:
            response = requests.put(url, json=payload, auth=self._get_auth())
            response.raise_for_status()
            updated_group = response.json()
            print(f"✓ Successfully updated saved group: {group_id}")
            return group_id
        except requests.exceptions.RequestException as e:
            print(f"✗ Error updating saved group '{group_id}': {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def ensure_saved_group(self, name, condition, description="", projects=None):
        """
        Ensure a saved group exists with the given configuration.
        Creates it if missing, updates it if exists.
        
        Args:
            name (str): The display name.
            condition (dict or str): The condition logic.
            description (str, optional): Description.
            projects (list, optional): List of project IDs.
            
        Returns:
            str: The ID of the created or updated saved group, or None if failed.
        """
        # Ensure cache is populated at least once
        if not self._is_saved_groups_cache_loaded:
            self.list_saved_groups()
        
        # Check if group exists in cache by name
        existing = self.saved_groups_cache.get(name)
        
        if projects is None and self.project:
            projects = [self.project]
        elif projects is None:
            projects = []

        if isinstance(condition, dict):
            condition_str = json.dumps(condition)
        else:
            condition_str = str(condition)

        payload = {
            "type": "condition",
            "name": name,
            "owner": self.owner,
            "condition": condition_str,
            "projects": projects
        }
        
        if existing:
            # Get the group ID from the existing group
            group_id = existing.get("id")
            # print(f"Saved group '{name}' already exists. Updating...")
            return group_id
        else:
            return self.create_saved_group(name, condition, projects)



# Example Usage
if __name__ == "__main__":
    # Replace with your actual API Key
    API_KEY = "secret_user_pZ0b0Qu6vE2iaGHjbH6xj3kyDksZm79y7HOsyxuMzLw" 
    
    gb = GrowthBook(api_key=API_KEY)
    
    # 1. List attributes (will populate cache)
    # print("Fetching attributes...")
    # attrs = gb.list_attributes()
    # print(f"Found {len(attrs)} attributes.")

    # # 2. Check for an attribute that might not exist, auto-create if missing
    # # Example: 'is_premium_user'
    # attr_name = "nam_dep_trai"
    # attribute = gb.ensure_attribute(attr_name, datatype="string")
    
    # if attribute:
    #     print(f"Attribute details: {attribute}")
    feature = gb.get_feature("APP_DOWNLOAD_LINK_NORMAL")
    print(feature)

