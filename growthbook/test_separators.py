from growthbook_client import GrowthBook

# Test the unsupported separator detection
gb = GrowthBook(api_key="test_key")

# Test config with various separators
test_config = {
    'default': ['https://swag.live/default'],
    'country=cn': ['https://sst011.fyfys.cn'],  # Should work (simple key=value)
    'utm_campaign=my_routine&utm_medium=non-rtb&utm_source=cheongdb2u': ['https://swag.live/campaign'],  # Should work (ampersand with hyphen in value)
    'utm_campaign=test&utm_medium=email': ['https://swag.live/campaign2'],  # Should work (ampersand)
    'utm_campaign=telegram_04;utm_content=20230303;utm_medium=non-rtb;utm_source=telegram': ['https://i.imgur.com/IuINI1N.jpg'],  # Should skip (semicolon)
    'beta': ['https://swag.live/beta'],  # Should work (simple key)
    'key=value-key2=value2': ['https://test.com'],  # Should skip (hyphen separator, NOT ampersand)
}

print("Testing process_config_to_rules with various separators...")
print("=" * 70)
default_val, rules, val_type, attrs, skipped = gb.process_config_to_rules(
    test_config, 
    config_key="TEST_CONFIG"
)

print(f"\n{'=' * 70}")
print(f"Results:")
print(f"{'=' * 70}")
print(f"Default: {default_val}")
print(f"Rules created: {len(rules)}")
print(f"Attributes needed: {attrs}")
print(f"Skipped keys: {len(skipped)}")

print(f"\n{'=' * 70}")
print(f"Rules Details:")
print(f"{'=' * 70}")
for i, rule in enumerate(rules, 1):
    print(f"{i}. {rule['description']}")
    print(f"   Condition: {rule['condition']}")
    print(f"   Value: {rule['value'][:50]}..." if len(str(rule['value'])) > 50 else f"   Value: {rule['value']}")

if skipped:
    print(f"\n{'=' * 70}")
    print(f"Skipped Details:")
    print(f"{'=' * 70}")
    for i, skip in enumerate(skipped, 1):
        print(f"{i}. {skip['child_key']}")
        print(f"   Reason: {skip['reason']}")

