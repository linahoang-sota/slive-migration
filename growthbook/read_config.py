import yaml
import os

def read_configuration(file_path):
    """
    Reads a YAML configuration file and returns the data as a dictionary.

    Args:
        file_path (str): The path to the configuration.yaml file.

    Returns:
        dict: The configuration data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            config_data = yaml.safe_load(file)
            return config_data
        except yaml.YAMLError as exc:
            print(f"Error reading YAML file: {exc}")
            return None

def main():
    # Example usage
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_dir, 'configuration.yaml')
    
    print(f"Reading configuration from: {config_file_path}")
    
    config = read_configuration(config_file_path)
    
    if config:
        print("Configuration loaded successfully!")
        # Print first few keys to verify
        print("Top-level keys found:", list(config.keys())[:5])
        
        # Example: Accessing a specific key if it exists
        key_to_check = 'USER_EVENT_REPORT_URL'
        if key_to_check in config:
             print(f"{key_to_check}: {config[key_to_check]}")
    else:
        print("Failed to load configuration.")

if __name__ == "__main__":
    main()
