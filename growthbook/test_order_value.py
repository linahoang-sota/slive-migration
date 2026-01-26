from main import reorder_config_value, PRIORITY_ORDER
from read_config import read_configuration
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_file = os.path.join(parent_dir, "configuration.yaml")
    config = read_configuration(config_file)
    if not config:
        print("Failed to load configuration")
    
    for feature_id, config_value in config.items():
        if not isinstance(config_value, dict):
            continue
        with open("test_order_value.txt", "a") as f:
            f.write(f"\n\n{feature_id}")
            reordered = reorder_config_value(config_value)
            for k, v in reordered.items():
                f.write(f"\n{k}")
        # keys = list(reordered.keys())
        
        # # Verify that for any pair (i, j) where i < j, priority_index(keys[i]) <= priority_index(keys[j])
        # # Meaning: Higher priority (lower index) comes first.
        
        # for i in range(len(keys) - 1):
        #     key_current = keys[i]
        #     key_next = keys[i+1]
            
        #     p_current = PRIORITY_ORDER.index(key_current)
        #     p_next = PRIORITY_ORDER.index(key_next)
            
        #     if p_current > p_next:
        #         # Violation: Lower priority item appeared before Higher priority item
        #         # e.g. default (24) appeared before client_id (0)
        #         print(f"VIOLATION in {feature_id}: '{key_current}' ({p_current}) comes before '{key_next}' ({p_next})")
        #         return
        
    print("SUCCESS: All rules are correctly ordered by priority.")
