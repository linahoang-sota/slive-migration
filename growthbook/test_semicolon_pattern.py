#!/usr/bin/env python3
"""
Test script to verify semicolon-separated pattern support.
"""

import os
from growthbook_client import GrowthBook

# Configuration
API_KEY = os.getenv("GROWTHBOOK_API_KEY", "secret_user_pZ0b0Qu6vE2iaGHjbH6xj3kyDksZm79y7HOsyxuMzLw")
API_URL = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100/api/v1")
PROJECT = os.getenv("GROWTHBOOK_PROJECT", "prj_a01tmkkm7zc9")
OWNER = os.getenv("GROWTHBOOK_OWNER", "nam.nguyen23@sotatek.com")

def test_semicolon_separated():
    """Test semicolon-separated pattern (utm_campaign=x;utm_medium=y)"""
    print("\n" + "="*60)
    print("TEST: Semicolon-Separated Pattern")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_value"],
        "utm_campaign=test;utm_medium=email": ["semicolon_value"],
        "utm_campaign=promo&utm_source=web": ["ampersand_value"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_SEMICOLON"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Value Type: {value_type}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Skipped Keys: {len(skipped_keys)}")
    
    if skipped_keys:
        print("\n⚠ Skipped Keys:")
        for skipped in skipped_keys:
            print(f"  - {skipped}")
    
    if rules:
        print("\n📋 Generated Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Value: {rule.get('value')}")
            print(f"    Description: {rule.get('description')}")
            print(f"    Enabled: {rule.get('enabled')}")
            print(f"    SavedGroupTargeting: {rule.get('savedGroupTargeting')}")
            
            # Verify structure
            assert 'savedGroupTargeting' in rule, "Should have savedGroupTargeting"
            assert len(rule['savedGroupTargeting']) > 0, "Should have at least one targeting rule"
            assert rule['savedGroupTargeting'][0]['matchType'] == 'all', "Match type should be 'all'"
            assert len(rule['savedGroupTargeting'][0]['savedGroups']) > 0, "Should have at least one saved group ID"
    
    # Verify both patterns were processed (not skipped)
    assert len(rules) == 2, f"Expected 2 rules (semicolon and ampersand), got {len(rules)}"
    assert len(skipped_keys) == 0, f"Expected 0 skipped keys, got {len(skipped_keys)}"
    
    print("\n✅ TEST PASSED - Semicolon-separated patterns are now supported!")
    return True

def test_mixed_separators():
    """Test that we can handle both & and ; in the same config"""
    print("\n" + "="*60)
    print("TEST: Mixed Separators (& and ;)")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_url"],
        "country=cn": ["china_url"],
        "utm_campaign=email;utm_medium=newsletter": ["email_newsletter_url"],
        "utm_campaign=social&utm_source=facebook": ["social_facebook_url"],
        "beta": ["beta_url"]
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_MIXED_SEPARATORS"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Attributes Needed: {attributes_needed}")
    print(f"✓ Skipped Keys: {len(skipped_keys)}")
    
    # Should have 4 rules: country=cn, semicolon pattern, ampersand pattern, beta
    assert len(rules) == 4, f"Expected 4 rules, got {len(rules)}"
    assert len(skipped_keys) == 0, f"Expected 0 skipped keys, got {len(skipped_keys)}"
    
    print("\n📋 Rule Descriptions:")
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule.get('description')}")
    
    print("\n✅ TEST PASSED - Mixed separators work correctly!")
    return True

def test_hyphen_still_unsupported():
    """Test that hyphen-separated patterns are still unsupported"""
    print("\n" + "="*60)
    print("TEST: Hyphen-Separated Pattern (Should be Skipped)")
    print("="*60)
    
    gb = GrowthBook(api_key=API_KEY, api_url=API_URL, project=PROJECT, owner=OWNER)
    
    config_value = {
        "default": ["default_value"],
        "utm_campaign=test-utm_medium=email": ["hyphen_value"]  # Should be skipped
    }
    
    default_value, rules, value_type, attributes_needed, skipped_keys = gb.process_config_to_rules(
        config_value=config_value,
        config_key="TEST_HYPHEN"
    )
    
    print(f"\n✓ Default Value: {default_value}")
    print(f"✓ Number of Rules: {len(rules)}")
    print(f"✓ Skipped Keys: {len(skipped_keys)}")
    
    # Hyphen pattern should be skipped
    assert len(rules) == 0, f"Expected 0 rules (hyphen should be skipped), got {len(rules)}"
    assert len(skipped_keys) == 1, f"Expected 1 skipped key, got {len(skipped_keys)}"
    
    if skipped_keys:
        print("\n✓ Correctly skipped:")
        for skipped in skipped_keys:
            print(f"  - {skipped.get('child_key')}: {skipped.get('reason')}")
    
    print("\n✅ TEST PASSED - Hyphen-separated patterns are still correctly skipped!")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SEMICOLON-SEPARATED PATTERN VERIFICATION")
    print("="*60)
    
    tests = [
        ("Semicolon-Separated Pattern", test_semicolon_separated),
        ("Mixed Separators", test_mixed_separators),
        ("Hyphen Still Unsupported", test_hyphen_still_unsupported)
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
        print("\nSemicolon-separated patterns (utm_campaign=x;utm_medium=y)")
        print("are now supported alongside ampersand-separated patterns!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
