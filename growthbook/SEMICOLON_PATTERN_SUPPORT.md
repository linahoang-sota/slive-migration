# Semicolon-Separated Pattern Support

## Overview
Updated `growthbook_client.py` to support semicolon-separated patterns (e.g., `utm_campaign=x;utm_medium=y`) in addition to ampersand-separated patterns.

## Changes Made

### 1. Updated `_has_unsupported_separator()` Function
**Before:** Semicolon-separated patterns were flagged as unsupported  
**After:** Semicolon-separated patterns are now treated as supported

```python
# Now supports both & and ; separators
if "&" in key or ";" in key:
    # These are supported multi-condition patterns
    return False
```

**Supported Patterns:**
- ✅ `key=value` (simple)
- ✅ `key1=value1&key2=value2` (ampersand-separated)
- ✅ `key1=value1;key2=value2` (semicolon-separated) **← NEW**

**Unsupported Patterns:**
- ❌ `key1=value1-key2=value2` (hyphen-separated)

### 2. Renamed `_parse_ampersand_conditions()` to `_parse_multi_conditions()`
**Purpose:** Handle both ampersand and semicolon separators

```python
def _parse_multi_conditions(self, condition_string):
    """
    Parse ampersand or semicolon-separated conditions.
    
    Examples:
    - "utm_campaign=test&utm_medium=email"
    - "utm_campaign=test;utm_medium=email"
    """
    # Determine the separator (& or ;)
    separator = "&" if "&" in condition_string else ";"
    
    # Split by the separator to get individual conditions
    parts = condition_string.split(separator)
    ...
```

### 3. Updated `process_config_to_rules()`
**Before:** Only checked for `&` in child_key  
**After:** Checks for both `&` and `;` in child_key

```python
# Handle ampersand or semicolon-separated conditions
if "&" in child_key or ";" in child_key:
    condition_dict, attrs = self._parse_multi_conditions(child_key)
    ...
```

### 4. Updated Documentation
- Updated docstrings to reflect semicolon support
- Added example in `process_config_to_rules` docstring:
  ```python
  'utm_campaign=a;utm_medium=b': ['value6']
  ```

## Test Results

Created `test_semicolon_pattern.py` with 3 comprehensive tests:

### Test 1: Semicolon-Separated Pattern ✅
- Input: `utm_campaign=test;utm_medium=email`
- Result: Successfully created saved group with ID `grp_a01tmkndwcsk`
- Verified: Pattern is NOT skipped, creates proper rule with savedGroupTargeting

### Test 2: Mixed Separators ✅
- Input: Mix of `;`, `&`, and simple patterns
- Result: All 4 rules created successfully
  1. `country=cn`
  2. `utm_campaign=email;utm_medium=newsletter`
  3. `utm_campaign=social&utm_source=facebook`
  4. `beta users`
- Verified: Both separator types work together

### Test 3: Hyphen Still Unsupported ✅
- Input: `utm_campaign=test-utm_medium=email`
- Result: Correctly skipped with reason `unsupported_separator_hyphen`
- Verified: Hyphen patterns are still rejected

## Usage Examples

### Before (Would be skipped):
```python
config_value = {
    "default": ["default_value"],
    "utm_campaign=promo;utm_medium=email": ["promo_email_value"]  # ❌ Skipped
}
```

### After (Now supported):
```python
config_value = {
    "default": ["default_value"],
    "utm_campaign=promo;utm_medium=email": ["promo_email_value"]  # ✅ Supported
}
```

Both create the same saved group structure:
```json
{
  "name": "utm_campaign=promo;utm_medium=email",
  "condition": "{\"utm_campaign\": \"promo\", \"utm_medium\": \"email\"}"
}
```

## Benefits

✅ **Backward Compatible:** Existing ampersand patterns still work  
✅ **Flexible:** Support for different separator preferences  
✅ **Consistent:** Both separators create identical saved group structures  
✅ **Validated:** Comprehensive test coverage confirms functionality  

## Migration Notes

- No changes needed for existing configurations using `&`
- Configurations using `;` will now be processed instead of skipped
- Check `except.json` - previously skipped semicolon patterns will now be processed
- Hyphen-separated patterns remain unsupported (by design)
