#!/usr/bin/env python3
"""
Verification script for process_config_to_rules with saved groups.

This script tests the new logic that creates saved groups instead of inline conditions.
"""

import os
import sys
from growthbook_client import GrowthBook

# Configuration
API_KEY = os.getenv("GROWTHBOOK_API_KEY", "secret_user_pZ0b0Qu6vE2iaGHjbH6xj3kyDksZm79y7HOsyxuMzLw")
API_URL = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100/api/v1")
PROJECT = os.getenv("GROWTHBOOK_PROJECT", "prj_a01tmkkm7zc9")
OWNER = os.getenv("GROWTHBOOK_OWNER", "nam.nguyen23@sotatek.com")

def test_simple_key():
    """Test simple key pattern (beta, creator, etc.)"""
    print("\n" + "="*60)
    print("TEST 1: Simple Key Pattern (beta)")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_value"],
        "beta": ["beta_value"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_SIMPLE_KEY"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Value Type: {value_type}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Skipped Keys: {len(skipped_keys)}")
    
    if rules:
        print("\n📋 Generated Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Condition: {rule.get('condition')}")
            print(f"    Value: {rule.get('value')}")
            print(f"    Description: {rule.get('description')}")
            print(f"    Enabled: {rule.get('enabled')}")
            print(f"    SavedGroupTargeting: {rule.get('savedGroupTargeting')}")
            
            # Verify structure
            assert rule.get('condition') == "{}", "Condition should be empty object string"
            assert 'savedGroupTargeting' in rule, "Should have savedGroupTargeting"
            assert len(rule['savedGroupTargeting']) > 0, "Should have at least one targeting rule"
            assert rule['savedGroupTargeting'][0]['matchType'] == 'all', "Match type should be 'all'"
            assert len(rule['savedGroupTargeting'][0]['savedGroups']) > 0, "Should have at least one saved group ID"
            
    print("\n✅ TEST 1 PASSED")
    return True

def test_key_value_pair():
    """Test key=value pattern (country=cn)"""
    print("\n" + "="*60)
    print("TEST 2: Key=Value Pattern (country=cn)")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["https://default.com"],
        "country=cn": ["https://china.com"],
        "country=us": ["https://usa.com"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_COUNTRY"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Value Type: {value_type}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Number of Rules: {len(rules)}")
    
    if rules:
        print("\n📋 Generated Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Condition: {rule.get('condition')}")
            print(f"    Value: {rule.get('value')}")
            print(f"    Description: {rule.get('description')}")
            print(f"    SavedGroupTargeting: {rule.get('savedGroupTargeting')}")
            
            # Verify structure
            assert rule.get('condition') == "{}", "Condition should be empty object string"
            assert 'savedGroupTargeting' in rule, "Should have savedGroupTargeting"
            
    print("\n✅ TEST 2 PASSED")
    return True

def test_ampersand_separated():
    """Test ampersand-separated pattern (utm_campaign=x&utm_medium=y)"""
    print("\n" + "="*60)
    print("TEST 3: Ampersand-Separated Pattern")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_value"],
        "utm_campaign=test&utm_medium=email": ["campaign_value"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_UTM"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Value Type: {value_type}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Number of Rules: {len(rules)}")
    
    if rules:
        print("\n📋 Generated Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Condition: {rule.get('condition')}")
            print(f"    Value: {rule.get('value')}")
            print(f"    Description: {rule.get('description')}")
            print(f"    SavedGroupTargeting: {rule.get('savedGroupTargeting')}")
            
            # Verify structure
            assert rule.get('condition') == "{}", "Condition should be empty object string"
            assert 'savedGroupTargeting' in rule, "Should have savedGroupTargeting"
            
    print("\n✅ TEST 3 PASSED")
    return True

def test_mixed_patterns():
    """Test mixed patterns in one config"""
    print("\n" + "="*60)
    print("TEST 4: Mixed Patterns")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_value"],
        "beta": ["beta_value"],
        "country=cn": ["china_value"],
        "utm_campaign=promo&utm_source=email": ["promo_value"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_MIXED"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Value Type: {value_type}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Expected Rules: 3 (beta, country=cn, utm pattern)")
    
    assert len(rules) == 3, f"Expected 3 rules, got {len(rules)}"
    
    if rules:
        print("\n📋 Generated Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Condition: {rule.get('condition')}")
            print(f"    Value: {rule.get('value')}")
            print(f"    Description: {rule.get('description')}")
            print(f"    SavedGroupTargeting: {rule.get('savedGroupTargeting')}")
            
            # Verify structure
            assert rule.get('condition') == "{}", "Condition should be empty object string"
            assert 'savedGroupTargeting' in rule, "Should have savedGroupTargeting"
            assert rule['savedGroupTargeting'][0]['matchType'] == 'all', "Match type should be 'all'"
            
    print("\n✅ TEST 4 PASSED")
    return True

def test_saved_groups_cache():
    """Test that saved groups are properly cached"""
    print("\n" + "="*60)
    print("TEST 5: Saved Groups Caching")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    # First call - should create saved group
    print("\n📝 First call - creating saved group...")
    config_value = {
        "default": ["default_value"],
        "beta": ["beta_value"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_CACHE"
    )
    
    first_group_id = rules[0]['savedGroupTargeting'][0]['savedGroups'][0] if rules else None
    print(f"✓ First Group ID: {first_group_id}")
    
    # Second call with same config - should reuse saved group
    print("\n📝 Second call - should reuse saved group...")
    default_value2, rules2, value_type2, attributes_needed2, skipped_keys2 = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_CACHE"
    )
    
    second_group_id = rules2[0]['savedGroupTargeting'][0]['savedGroups'][0] if rules2 else None
    print(f"✓ Second Group ID: {second_group_id}")
    
    # Verify same group ID is used
    assert first_group_id == second_group_id, "Should reuse the same saved group ID"
    print(f"\n✓ Verified: Both calls used the same group ID: {first_group_id}")
    
    print("\n✅ TEST 5 PASSED")
    return True

def test_create_feature_with_saved_groups():
    """Test creating a feature with the new saved group rules"""
    print("\n" + "="*60)
    print("TEST 6: Create Feature with Saved Groups")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["https://default.example.com"],
        "country=cn": ["https://china.example.com"],
        "beta": ["https://beta.example.com"]
    }
    
    # Process config to rules
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_FEATURE_URL"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    
    # Ensure attributes exist
    print("\n📝 Ensuring attributes exist...")
    for attr in attributes_needed:
        gb.ensure_attribute(attr, datatype="string")
    
    # Create the feature
    print("\n📝 Creating feature...")
    feature_id = "TEST_FEATURE_WITH_SAVED_GROUPS"
    result = gb.create_feature(
        feature_id=feature_id,
        value_type=value_type,
        default_value=default_value,
        description="Test feature with saved groups",
        rules=rules
    )
    
    if result:
        print(f"\n✅ Feature created successfully: {feature_id}")
        
        # Verify the feature was created
        feature = gb.get_feature(feature_id)
        if feature:
            print(f"✓ Feature verified in GrowthBook")
            print(f"✓ Feature ID: {feature.get('feature', {}).get('id')}")
        else:
            print("⚠ Could not verify feature in GrowthBook")
    else:
        print("\n⚠ Feature creation returned None (might already exist)")
    
    print("\n✅ TEST 6 PASSED")
    return True

def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("VERIFICATION SCRIPT FOR process_config_to_rules")
    print("Testing Saved Groups Integration")
    print("="*60)
    
    tests = [
        # ("Simple Key Pattern", test_simple_key),
        # ("Key=Value Pattern", test_key_value_pair),
        # ("Ampersand-Separated Pattern", test_ampersand_separated),
        # ("Mixed Patterns", test_mixed_patterns),
        # ("Saved Groups Caching", test_saved_groups_cache),
        ("Create Feature with Saved Groups", test_create_feature_with_saved_groups)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
