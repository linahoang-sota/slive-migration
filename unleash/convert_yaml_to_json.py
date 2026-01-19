#!/usr/bin/env python3
"""
Convert YAML configuration to JSON with structured format.
Conditions with '=' operator are grouped into nested objects.
"""

import yaml
import json
import re
from collections import OrderedDict


def parse_condition(condition_key):
    """
    Parse condition key like 'os=ios' into (parameter, value).
    Returns (None, None) if no '=' found (e.g., 'default', 'beta').
    """
    if '=' in condition_key:
        parts = condition_key.split('=', 1)
        return parts[0], parts[1]
    return None, None


def convert_yaml_to_json(yaml_data):
    """
    Convert YAML data to JSON with grouped conditions.
    """
    result = OrderedDict()
    
    for config_key, conditions in yaml_data.items():
        if not isinstance(conditions, dict):
            result[config_key] = conditions
            continue
            
        config_obj = OrderedDict()
        
        for condition_key, values in conditions.items():
            param, value = parse_condition(condition_key)
            
            if param is None:
                # Simple key like 'default' or 'beta'
                config_obj[condition_key] = values
            else:
                # Grouped key like 'os=ios'
                if param not in config_obj:
                    config_obj[param] = OrderedDict()
                config_obj[param][value] = values
        
        result[config_key] = config_obj
    
    return result


def main():
    # Read YAML file
    with open('/home/cuongbtq/scripts/configuration.yaml', 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    
    # Convert to structured JSON
    json_data = convert_yaml_to_json(yaml_data)
    
    # Write to JSON file
    output_file = '/home/cuongbtq/scripts/configuration.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Conversion complete! Output saved to: {output_file}")
    print(f"Total configuration keys: {len(json_data)}")


if __name__ == '__main__':
    main()
