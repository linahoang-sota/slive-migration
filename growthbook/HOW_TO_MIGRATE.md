# How to Migrate Configuration Keys to GrowthBook

This guide explains how to migrate configuration keys from `configuration.yaml` to GrowthBook feature flags.

---

## Prerequisites

1. **GrowthBook Account** with API access
2. **API Credentials**:
   - API Key
   - Project ID
   - Owner email
3. **Python Environment** with dependencies:
   ```bash
   pip install pyyaml requests
   ```

---

## Migration Steps

### Step 1: Understand Your Configuration Structure

Your YAML configuration follows this pattern:

```yaml
CONFIG_KEY_NAME:
  default:
    - default_value
  condition_key:
    - conditional_value
```

**Example**:
```yaml
USER_EVENT_REPORT_URL:
  default:
    - https://swag.live/battlepass/index.html
  country=cn:
    - https://sst011.fyfys.cn/battlepass/main/index.html
  country=my:
    - https://public.sophisticatedwondersasiangems.xyz/battlepass/main/index.html
```

### Step 2: Identify Configuration Patterns

Your configuration uses different patterns for conditions:

#### Pattern 1: Default Value
```yaml
default:
  - value
```
→ Becomes the feature flag's **default value**

#### Pattern 2: Simple User Roles
```yaml
beta:
  - value_for_beta_users
creator:
  - value_for_creators
```
→ Creates attribute `is_beta`, `is_creator` with boolean type

**Supported roles**: `beta`, `authenticated`, `verified`, `creator`, `curator`, `banned`, `nsfw`, `owner`

#### Pattern 3: Key=Value Conditions
```yaml
country=cn:
  - value_for_china
os=ios:
  - value_for_ios
```
→ Creates attributes `country`, `os` with string type

#### Pattern 4: Multiple Conditions (Ampersand)
```yaml
utm_campaign=test&utm_medium=email&utm_source=google:
  - value_for_this_combination
```
→ Creates attributes `utm_campaign`, `utm_medium`, `utm_source`  
→ Rule requires ALL conditions to match

---

## Step 3: Set Up Migration Script

### Configure Your Credentials

Edit `main.py`:

```python
# Replace with your actual credentials
GROWTHBOOK_API_KEY = "secret_user_xxxxx"
GROWTHBOOK_PROJECT = "prj_xxxxx"
GROWTHBOOK_OWNER = "your.email@company.com"
```

### Run the Migration

```bash
cd /path/to/configurations
python3 main.py
```

The script will:
1. ✅ Read `configuration.yaml`
2. ✅ Extract unique attributes from conditions
3. ✅ Create attributes in GrowthBook
4. ✅ Create feature flags with rules
5. ⚠️ Log unsupported patterns to `except.json`

---

## Step 4: Understanding the Conversion

### What Gets Created

For each configuration key, the script creates:

#### 1. Attributes (Targeting Conditions)

| YAML Condition | GrowthBook Attribute | Type |
|----------------|---------------------|------|
| `country=cn` | `country` | string |
| `os=ios` | `os` | string |
| `beta` | `is_beta` | boolean |
| `creator` | `is_creator` | boolean |
| `utm_campaign=test` | `utm_campaign` | string |

#### 2. Feature Flag

**Structure**:
```json
{
  "id": "CONFIG_KEY_NAME",
  "valueType": "string",
  "defaultValue": "value_from_default_key",
  "environments": {
    "production": {
      "enabled": true,
      "rules": [
        {
          "condition": "{\"country\": \"cn\"}",
          "value": "value_for_china"
        }
      ]
    }
  }
}
```

---

## Step 5: Handle Exceptions

After migration, check `except.json` for configurations that couldn't be auto-migrated.

### Common Exception Types

#### 1. Semicolon Separator (Unsupported)

**Problem**:
```yaml
utm_campaign=x;utm_medium=y:
  - value
```

**Solution**: Convert to ampersand separator
```yaml
utm_campaign=x&utm_medium=y:
  - value
```

Then re-run migration.

#### 2. Hyphen Separator (Unsupported)

**Problem**:
```yaml
key=value-key2=value2:
  - value
```

**Solution**: Convert to ampersand separator
```yaml
key=value&key2=value2:
  - value
```

#### 3. Unrecognized Pattern

**Problem**:
```yaml
some-random-pattern:
  - value
```

**Solutions**:
- **Option A**: Convert to supported format (e.g., `key=value`)
- **Option B**: Add to simple keys list if it's a user role
- **Option C**: Create manually in GrowthBook UI

---

## Step 6: Verify Migration

### Check in GrowthBook UI

1. **Navigate to Features**
   - Verify feature count matches config keys
   - Check feature IDs match YAML keys

2. **Navigate to Attributes**
   - Verify all targeting attributes exist
   - Check attribute types (string/boolean)

3. **Inspect Sample Features**
   - Open a feature flag
   - Verify default value
   - Check rules and conditions

### Validation Checklist

- [ ] All expected features created
- [ ] Attributes have correct types
- [ ] Default values are correct
- [ ] Rules match YAML conditions
- [ ] No critical configs in `except.json`

---

## Step 7: Manual Migration for Exceptions

For configurations in `except.json`:

### Option 1: Fix in YAML and Re-run

1. Edit `configuration.yaml`
2. Convert to supported pattern
3. Re-run migration script

### Option 2: Create Manually in GrowthBook

1. **Go to GrowthBook UI** → Features → Add Feature
2. **Set Feature Details**:
   - ID: `CONFIG_KEY_NAME`
   - Value Type: Choose appropriate type
   - Default Value: Value from `default` key

3. **Create Attributes** (if needed):
   - Go to Attributes → Add Attribute
   - Set property name and type

4. **Add Rules**:
   - Click "Add Rule" in feature
   - Set condition (e.g., `country = cn`)
   - Set value for this condition

---

## Migration Examples

### Example 1: Simple Configuration

**YAML**:
```yaml
API_URL_PREFIX:
  default:
    - https://api.swag.live
  country=cn:
    - https://api.sst011.fyfys.cn
  country=my:
    - https://api.my.swag.live
```

**GrowthBook Result**:
- **Feature**: `API_URL_PREFIX`
- **Default**: `https://api.swag.live`
- **Attribute**: `country` (string)
- **Rules**:
  - `country = cn` → `https://api.sst011.fyfys.cn`
  - `country = my` → `https://api.my.swag.live`

### Example 2: User Role Configuration

**YAML**:
```yaml
FEATURE_LIVESTREAM:
  default:
    - ''
  creator:
    - '1'
  beta:
    - '1'
```

**GrowthBook Result**:
- **Feature**: `FEATURE_LIVESTREAM`
- **Default**: `''`
- **Attributes**: `is_creator` (boolean), `is_beta` (boolean)
- **Rules**:
  - `is_creator = true` → `'1'`
  - `is_beta = true` → `'1'`

### Example 3: Multiple Conditions

**YAML**:
```yaml
LANDING_MOBILE_COVER:
  default:
    - https://sw4g.shop/img/bg-mobile.jpg
  utm_campaign=my_routine&utm_medium=non-rtb&utm_source=cheongdb2u:
    - https://i.imgur.com/G4KGidV.jpg
```

**GrowthBook Result**:
- **Feature**: `LANDING_MOBILE_COVER`
- **Default**: `https://sw4g.shop/img/bg-mobile.jpg`
- **Attributes**: `utm_campaign`, `utm_medium`, `utm_source` (all string)
- **Rules**:
  - `utm_campaign = my_routine` AND `utm_medium = non-rtb` AND `utm_source = cheongdb2u` → `https://i.imgur.com/G4KGidV.jpg`

---

## Troubleshooting

### Issue: Rate Limit Exceeded

**Error**: HTTP 429 from GrowthBook API

**Solution**: Script already includes 1-second delay. If still hitting limits:
```python
# In main.py, increase sleep time
sleep(2)  # Instead of sleep(1)
```

### Issue: Attribute Already Exists

**Error**: Attribute creation fails

**Solution**: Script automatically handles this with `ensure_attribute()`. No action needed.

### Issue: Invalid Condition Format

**Error**: Feature created but condition doesn't work

**Solution**: 
1. Check `except.json` for the config
2. Verify condition follows supported patterns
3. Manually fix in GrowthBook UI if needed

### Issue: Value Type Mismatch

**Error**: Feature has wrong value type

**Solution**: Script infers type from default value. To override:
1. Delete feature in GrowthBook
2. Manually create with correct type
3. Add rules

---

## Best Practices

### Before Migration

1. ✅ **Backup** `configuration.yaml`
2. ✅ **Test** with a small subset first
3. ✅ **Document** any custom patterns in your config
4. ✅ **Review** `except.json` from test run

### During Migration

1. ✅ **Monitor** console output for errors
2. ✅ **Check** `except.json` periodically
3. ✅ **Verify** sample features in GrowthBook UI
4. ✅ **Track** progress (features created vs total)

### After Migration

1. ✅ **Validate** all critical configurations
2. ✅ **Test** application with GrowthBook SDK
3. ✅ **Document** manual changes made
4. ✅ **Archive** migration logs

---

## Quick Reference

### Supported Patterns

| Pattern | Example | Creates |
|---------|---------|---------|
| Default | `default: [value]` | Default value |
| Simple role | `beta: [value]` | `is_beta` boolean attribute |
| Key=value | `country=cn: [value]` | `country` string attribute |
| Multiple | `key1=val1&key2=val2: [value]` | Multiple string attributes |

### Unsupported Patterns

| Pattern | Example | Action |
|---------|---------|--------|
| Semicolon | `key1=val1;key2=val2` | Convert to `&` |
| Hyphen | `key1=val1-key2=val2` | Convert to `&` |
| Unknown | `random-pattern` | Manual creation |

---

## Files Generated

| File | Description |
|------|-------------|
| `except.json` | Configurations that need manual review |
| GrowthBook Features | One per configuration key |
| GrowthBook Attributes | Targeting conditions |

---

## Need Help?

- **Review**: `MIGRATION_SIMPLE.md` for overview
- **Check**: `except.json` for specific issues
- **Contact**: nam.nguyen@sotatek.com

---

## Summary

1. ✅ Configure credentials in `main.py`
2. ✅ Run `python3 main.py`
3. ⚠️ Review `except.json` for exceptions
4. 🔧 Fix exceptions (update YAML or create manually)
5. ✅ Verify in GrowthBook UI
6. 🚀 Integrate GrowthBook SDK in application

**That's it!** Your configurations are now in GrowthBook.
