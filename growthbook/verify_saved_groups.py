from growthbook_client import GrowthBook
import os
import json
import random
import string
import requests

def get_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def verify_saved_groups():
    # Hardcoded credentials for verification
    API_KEY = "secret_user_pZ0b0Qu6vE2iaGHjbH6xj3kyDksZm79y7HOsyxuMzLw"
    PROJECT_ID = "prj_a01tmkkm7zc9"
    OWNER = "nam.nguyen23@sotatek.com"
    API_URL = "http://localhost:3100/api/v1"
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT_ID, owner=OWNER)
    
    group_id = f"test_group_{get_random_string()}"
    group_name = f"Test Group {get_random_string()}"
    condition = {"country": "vn"}
    
    print(f"Testing Saved Group: {group_id}")

    # DEBUG: List saved groups
    print("DEBUG: Listing saved groups...")
    try:
        resp = requests.get(f"{API_URL}/saved-groups", auth=(API_KEY, ""))
        if resp.status_code == 200:
            data = resp.json()
            # print(f"List response: {json.dumps(data, indent=2)}")
            # Usually data is list or {savedGroups: []}
            groups = data.get("savedGroups", []) if isinstance(data, dict) else data
            if groups and len(groups) > 0:
                print(f"Sample Group: {json.dumps(groups[0], indent=2)}")
            else:
                print("No saved groups found.")
        else:
            print(f"List failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"List error: {e}")
    
    # 1. Test Ensure (Create)
    print("\n--- Test 1: Ensure (Create) ---")
    created = gb.ensure_saved_group(
        name=group_name,
        condition=condition,
        description="Auto-created by verification script"
    )
    
    if created:
        print(f"✅ Created/Ensured group: {created}")
    else:
        print("❌ Failed to create group")
        return

    # 2. Test Ensure (Update)
    print("\n--- Test 2: Ensure (Update) ---")
    new_condition = {"country": "us"}
    updated = gb.ensure_saved_group(
        name=group_name,
        condition=new_condition,
        description="Updated description"
    )
    
    if updated:
        print("✅ Ensure (Update) returned success.")
        # Verify content if possible (though PUT return value might be enough)
    else:
        print("❌ Failed to update group")

    # 3. Get Verify
    print("\n--- Test 3: Get ---")
    fetched = gb.get_saved_group(group_id)
    if fetched:
        cond = fetched.get("condition")
        print(f"Fetched condition: {cond}")
        # Note: condition comes back as string sometimes or parsed? API docs say string.
        if "us" in str(cond):
             print("✅ Condition verified updated to 'us'")
        else:
             print(f"⚠ Condition mismatch. Expected 'us' in {cond}")
    else:
        print("❌ Failed to get group")

if __name__ == "__main__":
    verify_saved_groups()
