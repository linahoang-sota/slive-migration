from read_config import read_configuration
from growthbook_client import GrowthBook
import os
from time import sleep
from dotenv import load_dotenv
from constants import PRIORITY_ORDER


def reorder_config_value(config_value):
    """
    Reorder configuration dictionary based on priority list.
    Ensures that high-priority rules are evaluated first in GrowthBook.
    
    GrowthBook evaluation is top-down (first matching rule wins).
    Rules are processed in the order they appear in config_value.
    Therefore, we need to sort the config_value such that:
    - High Priority items (e.g. client_id) are at the START of the dict.
    - Low Priority items (e.g. default/country) are at the END of the dict.
    
    Args:
        config_value (dict): Dictionary of configuration conditions.
        
    Returns:
        dict: Reordered dictionary.
    """
    if not isinstance(config_value, dict):
        return config_value

    def get_priority_index(key):
        # Normalize key (remove =value)
        key_base = key.split('=')[0]
        
        # Check for exact match or startswith match in priority list
        for i, priority_key in enumerate(PRIORITY_ORDER):
            if key_base == priority_key or key_base.startswith(priority_key):
                return i
        
        # If not found, assign high index (Low Priority)
        return len(PRIORITY_ORDER)

    # Sort items by priority index ASCENDING (High Priority = Low Index = First)
    sorted_items = sorted(
        config_value.items(),
        key=lambda item: get_priority_index(item[0])
    )
    
    return dict(sorted_items)



def process_config_element(config_key, config_value, growthbook_client):
    """
    Process a single configuration element: ensure attributes exist, then create feature flag.

    Flow:
    1. Process config_value into rules using process_config_to_rules() (which extracts attributes)
    2. Ensure each attribute exists in GrowthBook (create if missing)
    3. Create feature flag with the config_key as feature_id

    Args:
        config_key (str): The top-level configuration key (e.g., 'USER_EVENT_REPORT_URL')
        config_value (dict): The configuration value containing child keys (e.g., {'default': [...], 'country=cn': [...], ...})
        growthbook_client (GrowthBook): An instance of the GrowthBook client

    Returns:
        dict: The created feature flag data, or None if failed
    """
    if not isinstance(config_value, dict):
        print(f"Skipping {config_key}: value is not a dictionary")
        return None

    print(f"\n=== Processing Config: {config_key} ===")
    
    # Step 0: Reorder config_value based on priority
    config_value = reorder_config_value(config_value)

    # Step 1: Process config_value into rules (also extracts needed attributes)
    print(f"Processing config into feature rules...")
    default_value, rules, value_type, attributes_needed, skipped_keys = (
        growthbook_client.process_config_to_rules(config_value, config_key=config_key)
    )

    print(f"  - Default value: {default_value}")
    print(f"  - Value type: {value_type}")
    print(f"  - Number of rules: {len(rules)}")
    print(f"  - Attributes needed: {attributes_needed}")
    if skipped_keys:
        print(f"  - Skipped keys: {len(skipped_keys)}")

    # Step 2: Ensure all attributes exist
    print(f"\nEnsuring {len(attributes_needed)} attributes exist...")
    for attribute_name in attributes_needed:
        # Determine datatype based on attribute name
        # Boolean attributes (is_*) should be boolean type
        if attribute_name.startswith("is_"):
            datatype = "boolean"
        else:
            datatype = "string"

        description = f"Auto-created attribute from configuration.yaml"

        # Ensure the attribute exists (will create if missing)
        attribute = growthbook_client.ensure_attribute(
            property_key=attribute_name, datatype=datatype, description=description
        )

        if attribute:
            print(f"  ✓ Ensured attribute: {attribute_name} (type: {datatype})")
        else:
            print(f"  ✗ Failed to ensure attribute: {attribute_name}")

    # Step 3: Create feature flag
    print(f"\nCreating feature flag: {config_key}")
    feature = growthbook_client.create_feature(
        feature_id=config_key,
        value_type=value_type,
        default_value=default_value,
        description=f"Auto-generated feature from configuration.yaml",
        rules=rules,
        environment="production",
    )

    return feature


def infer_datatype(value):
    """
    Infer the GrowthBook datatype from a configuration value.

    Args:
        value: The configuration value

    Returns:
        str: The inferred datatype ('string', 'number', 'boolean', 'string[]')
    """
    if isinstance(value, list):
        return "string[]"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, (int, float)):
        return "number"
    else:
        return "string"


def process_all_config(config_file_path, growthbook_client):
    """
    Process all configuration elements and create GrowthBook feature flags.

    Args:
        config_file_path (str): Path to the configuration.yaml file
        api_key (str): GrowthBook API key

    Returns:
        dict: Summary of processed features
    """
    # Read configuration
    config = read_configuration(config_file_path)
    if not config:
        print("Failed to load configuration")
        return None

    # Initialize GrowthBook client
    gb = growthbook_client

    # Process each top-level configuration element
    total_features = 0
    processed_keys = 0

    for config_key, config_value in config.items():
        print(f"\n{'='*60}")
        print(f"Processing: {config_key}")
        print(f"{'='*60}")

        feature = process_config_element(config_key, config_value, gb)
        if feature:
            total_features += 1
        processed_keys += 1
        # Growthbook has limit to 60 requests per minute
        sleep(3)
        # if processed_keys == 50:
        #     break
            # print(f"Processed {processed_keys} configuration keys")

    summary = {"processed_keys": processed_keys, "total_features": total_features}

    print(f"\n{'='*60}")
    print(f"=== Summary ===")
    print(f"{'='*60}")
    print(f"Processed {processed_keys} configuration keys")
    print(f"Created {total_features} feature flags in GrowthBook")

    return summary


if __name__ == "__main__":
    # Configuration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_file = os.path.join(parent_dir, "configuration.yaml")
    
    # Load environment variables
    load_dotenv()

    # Get credentials from environment variables
    GROWTHBOOK_API_KEY = os.getenv("GROWTHBOOK_API_KEY")
    GROWTHBOOK_PROJECT = os.getenv("GROWTHBOOK_PROJECT")
    GROWTHBOOK_OWNER = os.getenv("GROWTHBOOK_OWNER")
    GROWTH_BOOK_API_URL = os.getenv("GROWTHBOOK_API_URL")

    if not GROWTHBOOK_API_KEY:
        print("Error: GROWTHBOOK_API_KEY not found in environment variables")
        exit(1)

    growthbook_client = GrowthBook(
        api_key=GROWTHBOOK_API_KEY,
        project=GROWTHBOOK_PROJECT,
        owner=GROWTHBOOK_OWNER,
        api_url=GROWTH_BOOK_API_URL,
    )

    # Process all configuration
    process_all_config(config_file, growthbook_client)
