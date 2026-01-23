# Configuration.yaml to GrowthBook Migration Plan

## Executive Summary

This document outlines the comprehensive migration plan for transitioning the SWAG Live application's configuration management from a static `configuration.yaml` file to GrowthBook's dynamic feature flag system. This migration will enable real-time configuration updates, A/B testing capabilities, and improved configuration management across multiple environments.

### Migration Scope

- **Configuration Keys**: 980 keys to migrate
- **Unique Attributes**: 26 targeting attributes
- **Exceptions**: ~4 configurations requiring manual review
- **Success Rate**: ~99.6% automated migration

---

## Table of Contents

1. [Overview](#1-overview)
2. [Migration Architecture](#2-migration-architecture)
3. [Supported Configuration Patterns](#3-supported-configuration-patterns)
4. [Migration Components](#4-migration-components)
5. [Migration Process](#5-migration-process)
6. [Exception Handling](#6-exception-handling)
7. [Testing Strategy](#7-testing-strategy)
8. [Rollback Plan](#8-rollback-plan)
9. [Appendices](#9-appendices)
10. [Client Integration Guide](#10-client-integration-guide)

---

## 1. Overview

### 1.1 Current State

The SWAG Live application currently uses a static YAML configuration file (`configuration.yaml`) with:
- **980 configuration keys**
- **7,288 lines** of configuration
- **Multiple environment-specific settings** (default, beta, country-specific, etc.)
- **Complex conditional logic** based on 26 unique attributes

### 1.2 Target State

Migrate to GrowthBook feature flags with:
- **980 feature flags** (one per configuration key)
- **26 attributes** for targeting conditions
- **Dynamic feature management** through GrowthBook UI
- **Real-time configuration updates** without deployment
- **Environment-specific rule sets**

### 1.3 Migration Statistics

| Metric                       | Count        |
| ---------------------------- | ------------ |
| **Total Configuration Keys** | 980          |
| **Feature Flags to Create**  | 980          |
| **Unique Attributes**        | 26           |
| **Automated Migrations**     | 976 (~99.6%) |
| **Manual Review Required**   | 4 (<1%)      |

### 1.4 Benefits

1. **Operational Efficiency**
   - No deployment required for configuration changes
   - Real-time updates across all instances
   - Reduced configuration errors

2. **Enhanced Capabilities**
   - A/B testing for configuration values
   - Gradual rollout of configuration changes
   - User segmentation based on 26 attributes

3. **Improved Governance**
   - Audit trail for all configuration changes
   - Role-based access control
   - Version history and rollback capabilities

---

## 2. Migration Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Migration Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  configuration.yaml (980 keys)                              │
│                                                             │
│         ▼                                                   │
│  read_config.py ──────► Parse YAML                          │
│         │                                                   │
│         ▼                                                   │
│  main.py ──────────────► Process Each Config Element        │
│         │                                                   │
│         ▼                                                   │
│  growthbook_client.py ─► Extract Attributes & Rules         │
│         │                                                   │
│         ├──────────────► Create 26 Attributes               │
│         │                                                   │
│         └──────────────► Create 980 Feature Flags           │
│                                                             │
│  Outputs:                                                   │
│  • 980 Feature Flags in GrowthBook                          │
│  • 26 Attributes in GrowthBook                              │
│  • except.json (16 exceptions)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

1. **Read Configuration**: Parse `configuration.yaml` (980 keys)
2. **Extract Attributes**: Identify 26 unique attributes from conditional keys
3. **Create Attributes**: Ensure all 26 attributes exist in GrowthBook
4. **Build Rules**: Convert configuration conditions into GrowthBook rules
5. **Create Features**: Generate 980 feature flags with appropriate rules
6. **Log Exceptions**: Track 4 unsupported patterns in `except.json`

---

## 3. Supported Configuration Patterns

### 3.1 Fully Supported Patterns

#### 3.1.1 Default Value
```yaml
CONFIG_KEY:
  default:
    - value
```
**Conversion**: Used as the feature flag's default value

#### 3.1.2 Simple Keys (User Roles)
```yaml
CONFIG_KEY:
  beta:
    - beta_value
  creator:
    - creator_value
  authenticated:
    - auth_value
```
**Supported Keys**: `beta`, `authenticated`, `verified`, `creator`, `curator`, `banned`, `nsfw`, `owner`

**Conversion**: 
- **Saved Group**: Created for each role (e.g., `beta` group with condition `{"is_beta": "true"}`)
- **Rule**: Targets the specific Saved Group
- Attribute: `is_<key>` (e.g., `is_beta`)
- Type: Boolean

**Attributes Created**: `is_beta`, `is_authenticated`, `is_verified`, `is_creator`, `is_curator`, `is_nsfw`

#### 3.1.3 Key=Value Pairs
```yaml
CONFIG_KEY:
  country=cn:
    - china_value
  os=ios:
    - ios_value
```
**Conversion**:
- **Saved Group**: Created for each condition (e.g., `country=cn`)
- **Rule**: Targets the Saved Group
- Attribute: `country`, `os`
- Condition: `{"country": "cn"}`, `{"os": "ios"}`
- Type: String

**Attributes Created**: `ab`, `browser`, `cohort`, `country`, `country-group`, `currency`, `flavor`, `forced-update`, `language`, `os`, `os_version`, `owner`, `pusher-app`, `suggested-update`, `utm_campaign`, `utm_content`, `utm_medium`, `utm_source`, `utm_term`

#### 3.1.4 Ampersand-Separated Conditions
```yaml
CONFIG_KEY:
  utm_campaign=test&utm_medium=email&utm_source=google:
    - value
```
**Conversion**:
- **Saved Group**: Created for the complex condition
- Attributes: `utm_campaign`, `utm_medium`, `utm_source`
- Condition: `{"utm_campaign": "test", "utm_medium": "email", "utm_source": "google"}`
- Type: String (all attributes)

**Note**: Hyphens within values are supported (e.g., `utm_medium=non-rtb`)

#### 3.1.5 Semicolon-Separated Conditions (New Support)
```yaml
CONFIG_KEY:
  utm_campaign=x;utm_medium=y:
    - value
```
**Conversion**:
- **Saved Group**: Created for the complex condition
- Condition: `{"utm_campaign": "x", "utm_medium": "y"}`

#### 3.1.6 Variants Key
Support for `variants` key usage for defining multiple variations via saved groups is fully integrated.

### 3.2 Unsupported Patterns (~4 Exceptions)

#### 3.2.1 Semicolon-Separated Conditions
**Now Supported**: Moved to Section 3.1.5.

#### 3.2.2 Unrecognized Patterns
**Count**: ~4 exceptions

**Examples**:
```yaml
CONFIG_KEY:
  some-unknown-pattern:
    - value
```
**Reason**: Pattern doesn't match any supported format  
**Action**: Logged to `except.json` for manual review

---

## 4. Migration Components

### 4.1 Core Scripts

#### 4.1.1 `read_config.py`
**Purpose**: Parse YAML configuration file

**Key Function**:
```python
def read_configuration(file_path) -> dict
```

**Responsibilities**:
- Load and parse `configuration.yaml`
- Handle YAML syntax errors
- Return 980 configuration keys as Python dictionary

#### 4.1.2 `growthbook_client.py`
**Purpose**: Interface with GrowthBook API

**Key Classes**:
```python
class GrowthBook:
    - list_attributes()
    - create_attribute()
    - ensure_attribute()
    - ensure_saved_group()
    - process_config_to_rules()
    - create_feature()
```

**Key Features**:
- Attribute caching to minimize API calls
- Automatic attribute creation (26 attributes)
- Rule generation from configuration patterns
- Exception logging for unsupported patterns

#### 4.1.3 `main.py`
**Purpose**: Orchestrate the migration process

**Key Functions**:
```python
def process_config_element(config_key, config_value, growthbook_client)
def process_all_config(config_file_path, growthbook_client)
```

**Responsibilities**:
- Iterate through 980 configuration keys
- Ensure 26 attributes exist
- Create 980 feature flags
- Rate limiting (1 request/second to respect API limits)

### 4.2 Configuration Files

#### 4.2.1 Input
- `configuration.yaml`: Source configuration file
  - 980 configuration keys
  - 7,288 lines
  - 26 unique attribute types

#### 4.2.2 Output
- **GrowthBook Features**: 980 feature flags
- **GrowthBook Attributes**: 26 attributes
- `except.json`: Log of 4 skipped configurations

---

## 5. Migration Process

### 5.1 Pre-Migration Checklist

- [ ] **Backup current configuration**
  - Create backup of `configuration.yaml`
  - Document current configuration state (980 keys)
  
- [ ] **GrowthBook Setup**
  - Create GrowthBook project
  - Generate API key with appropriate permissions
  - Configure project settings
  
- [ ] **Environment Preparation**
  - Install Python dependencies (`pyyaml`, `requests`, `python-dotenv`)
  - Configure API credentials
  - Set up logging directory

### 5.2 Migration Steps

#### Step 1: Initial Setup

1. **Configure GrowthBook Client**
   ```python
   GROWTHBOOK_API_KEY = "your_api_key"
   GROWTHBOOK_PROJECT = "your_project_id"
   GROWTHBOOK_OWNER = "your_email"
   ```

2. **Test Connection**
   ```bash
   python3 -c "from growthbook_client import GrowthBook; \
               gb = GrowthBook(api_key='YOUR_KEY'); \
               print(len(gb.list_attributes()))"
   ```

#### Step 2: Dry Run

1. **Run Migration Script**
   ```bash
   python3 main.py
   ```

2. **Review Output**
   - Check console output for errors
   - Review `except.json` for 16 skipped configurations
   - Verify attribute creation in GrowthBook UI (should see 26 attributes)

3. **Validate Sample Features**
   - Manually verify 10-20 feature flags
   - Check rule conditions
   - Verify default values

#### Step 3: Exception Resolution

1. **Analyze `except.json`** (4 exceptions)
   - Categorize skipped configurations
   - Determine resolution strategy for each

2. **Manual Migration**
   - Convert semicolon-separated to ampersand (~12 configs)
   - Handle unrecognized patterns (~4 configs)
   - Document decisions

3. **Update Configuration**
   - Modify `configuration.yaml` if needed
   - Re-run migration for updated entries

#### Step 4: Validation

1. **Automated Validation**
   - Compare feature count (expected: 980)
   - Verify all 26 attributes created
   - Check rule completeness

2. **Manual Validation**
   - Sample 50 random features
   - Verify complex conditions
   - Test edge cases

3. **Integration Testing**
   - Test application with GrowthBook SDK
   - Verify feature flag evaluation
   - Check performance impact

#### Step 5: Production Migration

1. **Final Backup**
   - Backup current GrowthBook state
   - Document all manual changes

2. **Execute Migration**
   - Run migration script
   - Monitor for errors
   - Track progress (980 features)

3. **Post-Migration Verification**
   - Verify 980 features created
   - Verify 26 attributes created
   - Test critical configurations
   - Monitor application logs

### 5.3 Rate Limiting Considerations

**GrowthBook API Limits**: 60 requests per minute

**Migration Strategy**:
- 1-second delay between feature creations
- Batch processing where possible
- Implement retry logic for rate limit errors

---

## 6. Exception Handling

### 6.1 Exception Categories

Based on current migration analysis, ~4 exceptions fall into these categories:

#### 6.1.1 Unrecognized Patterns (100%)

**Count**: ~4 exceptions

**Examples**:
```json
{
  "config_key": "PUSHER_APP_ID",
  "child_key": "pusher-app-web-ios",
  "reason": "unrecognized_pattern"
}
```

**Resolution Options**:
1. Add to supported simple keys list
2. Convert to key=value format
3. Create manually in GrowthBook

### 6.2 Exception Workflow

```
┌─────────────────────────────────────────┐
│     Migration Script Runs               │
│     (980 configurations)                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Unsupported Pattern Detected          │
│   (4 exceptions found)                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Log to except.json                    │
│   • config_key                          │
│   • child_key                           │
│   • reason                              │
│   • value                               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Manual Review (4 configs)             │
│   • Analyze pattern                     │
│   • Determine resolution                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Resolution Options                    │
│   1. Update configuration.yaml          │
│   2. Add to supported patterns          │
│   3. Create manually in GrowthBook      │
│   4. Mark as deprecated                 │
└─────────────────────────────────────────┘
```

---

## 7. Testing Strategy

### 7.1 Unit Testing

**Scope**: Individual components

**Test Cases**:
1. **YAML Parsing**
   - Valid YAML structure (980 keys)
   - Invalid YAML handling
   - Large file performance

2. **Pattern Recognition**
   - Simple keys detection
   - Key=value parsing
   - Ampersand separator parsing
   - Unsupported pattern detection

3. **Attribute Creation**
   - New attribute creation (26 attributes)
   - Existing attribute detection
   - Datatype inference

4. **Feature Creation**
   - Rule generation
   - Condition formatting
   - Default value handling

### 7.2 Integration Testing

**Scope**: End-to-end migration flow

**Test Scenarios**:
1. **Small Configuration Set**
   - 10 configuration keys
   - Various pattern types
   - Verify complete migration

2. **Medium Configuration Set**
   - 100 configuration keys
   - Include edge cases
   - Performance testing

3. **Full Configuration**
   - All 980 keys
   - Monitor rate limiting
   - Track 16 exceptions

### 7.3 Validation Testing

**Scope**: Verify migrated data

**Validation Points**:
1. **Feature Count**
   - Expected: 980 features
   - Actual: Count of features in GrowthBook

2. **Attribute Count**
   - Expected: 26 attributes
   - Actual: Count of attributes in GrowthBook

3. **Rule Accuracy**
   - Sample random features
   - Compare conditions with original YAML
   - Verify default values

4. **Application Integration**
   - Test with GrowthBook SDK
   - Verify feature evaluation
   - Check performance impact

---

## 8. Rollback Plan

### 8.1 Rollback Triggers

Execute rollback if:
- Migration fails for >10% of configurations (>98 features)
- Critical features are incorrectly migrated
- Application performance degrades significantly
- Data integrity issues detected

### 8.2 Rollback Procedure

#### Option 1: Revert to YAML (Immediate)

1. **Disable GrowthBook Integration**
   ```python
   # Revert to YAML-based configuration
   USE_GROWTHBOOK = False
   ```

2. **Restore YAML Configuration**
   ```bash
   cp configuration.yaml.backup configuration.yaml
   ```

3. **Restart Application**
   - Deploy with YAML configuration
   - Verify functionality

#### Option 2: Fix Forward (Preferred)

1. **Identify Issues**
   - Review error logs
   - Analyze failed features

2. **Correct in GrowthBook**
   - Fix feature flags manually
   - Update rules and conditions

3. **Validate Fixes**
   - Test corrected features
   - Monitor application behavior

### 8.3 Backup Strategy

**Before Migration**:
1. Export all GrowthBook features (if any exist)
2. Backup `configuration.yaml` (980 keys)
3. Document current application state

**During Migration**:
1. Log all API calls
2. Save migration output
3. Track created features (progress: X/980)

**After Migration**:
1. Export final GrowthBook state (980 features, 26 attributes)
2. Archive migration logs
3. Document changes

---

## 9. Appendices

### 9.1 Complete Attribute List

The migration will create these 26 attributes in GrowthBook:

| Attribute          | Type    | Description                |
| ------------------ | ------- | -------------------------- |
| `ab`               | string  | A/B test variant           |
| `banned`           | string  | Banned status              |
| `browser`          | string  | Browser type               |
| `cohort`           | string  | User cohort                |
| `country`          | string  | User country               |
| `country-group`    | string  | Country group              |
| `currency`         | string  | Currency type              |
| `flavor`           | string  | App flavor/variant         |
| `forced-update`    | string  | Force update flag          |
| `is_authenticated` | boolean | User authentication status |
| `is_beta`          | boolean | Beta user flag             |
| `is_creator`       | boolean | Creator role flag          |
| `is_curator`       | boolean | Curator role flag          |
| `is_nsfw`          | boolean | NSFW content flag          |
| `is_verified`      | boolean | Verified user flag         |
| `language`         | string  | User language              |
| `os`               | string  | Operating system           |
| `os_version`       | string  | OS version                 |
| `owner`            | string  | Owner identifier           |
| `pusher-app`       | string  | Pusher app identifier      |
| `suggested-update` | string  | Update suggestion flag     |
| `utm_campaign`     | string  | UTM campaign parameter     |
| `utm_content`      | string  | UTM content parameter      |
| `utm_medium`       | string  | UTM medium parameter       |
| `utm_source`       | string  | UTM source parameter       |
| `utm_term`         | string  | UTM term parameter         |

### 9.2 Migration Statistics

**Configuration Analysis**:

| Metric                     | Count | Percentage |
| -------------------------- | ----- | ---------- |
| Total Configuration Keys   | 980   | 100%       |
| Successfully Auto-Migrated | 976   | 99.6%      |
| Requires Manual Review     | 4     | 0.4%       |
| Unique Attributes          | 26    | -          |
| Configuration Lines        | 7,288 | -          |

**Exception Breakdown**:

| Exception Type       | Count | Percentage |
| -------------------- | ----- | ---------- |
| Semicolon Separator  | 12    | 75%        |
| Unrecognized Pattern | 4     | 25%        |
| **Total**            | **4** | **100%**   |

### 9.3 GrowthBook Feature Structure

#### Example Feature Flag

```json
{
  "id": "USER_EVENT_REPORT_URL",
  "description": "Auto-generated feature from configuration.yaml",
  "valueType": "string",
  "defaultValue": "https://swag.live/battlepass/index.html",
  "owner": "lina.hoang@sotatek.com",
  "project": "prj_7gxlgu1nmkjtaucm",
  "environments": {
    "production": {
      "enabled": true,
      "rules": [
        {
          "description": "country=cn",
          "condition": "{\"country\": \"cn\"}",
          "enabled": true,
          "type": "force",
          "value": "https://sst011.fyfys.cn/battlepass/main/index.html"
        }
      ]
    }
  }
}
```

### 9.4 Common Issues and Solutions

#### Issue 1: Rate Limit Exceeded
**Symptom**: HTTP 429 errors during migration

**Solution**:
```python
# Increase sleep time in main.py
sleep(2)  # Instead of sleep(1)
```

#### Issue 2: Attribute Already Exists
**Symptom**: Error when creating duplicate attributes
**Solution**: Script automatically handles this with `ensure_attribute()`

#### Issue 3: Invalid Condition Format
**Symptom**: Feature created but condition doesn't work
**Solution**: Verify JSON format in condition string

---

## 10. Client Integration Guide

To ensure feature flags are evaluated correctly, the client application must provide the following attributes in the GrowthBook context.

### 10.1 Required Attributes

#### Boolean Attributes (User State)
These attributes define the user's role or status. They map to simple configuration keys (e.g., `beta`, `creator`).

| Attribute          | Description             | Example |
| ------------------ | ----------------------- | ------- |
| `is_authenticated` | User is logged in       | `true`  |
| `is_banned`        | User is banned          | `false` |
| `is_beta`          | User is in beta program | `true`  |
| `is_creator`       | User is a creator       | `false` |
| `is_curator`       | User is a curator       | `false` |
| `is_nsfw`          | Allow NSFW content      | `true`  |
| `is_owner`         | User is an owner        | `false` |
| `is_verified`      | User is verified        | `true`  |

#### String Attributes (Targeting)
These attributes are used for specific targeting rules (e.g., `country=cn`).

| Attribute          | Description                       | Example         |
| ------------------ | --------------------------------- | --------------- |
| `ab`               | A/B Test Variant                  | `"A"`           |
| `browser`          | Browser Name                      | `"Chrome"`      |
| `cohort`           | User Cohort                       | `"123456"`      |
| `country`          | Country Code (ISO 3166-1 alpha-2) | `"cn"`          |
| `country-group`    | Group of countries                | `"europe"`      |
| `currency`         | User Currency                     | `"USD"`         |
| `flavor`           | App Flavor                        | `"live"`        |
| `forced-update`    | Forced Update Version             | `"1.2.0"`       |
| `language`         | User Language                     | `"en"`          |
| `os`               | Operating System                  | `"ios"`         |
| `os_version`       | OS Version                        | `"15.0"`        |
| `owner`            | Owner ID                          | `"user_123"`    |
| `pusher-app`       | Pusher App ID                     | `"app_key"`     |
| `suggested-update` | Suggested Update Version          | `"1.3.0"`       |
| `utm_campaign`     | UTM Campaign                      | `"summer_sale"` |
| `utm_content`      | UTM Content                       | `"banner"`      |
| `utm_medium`       | UTM Medium                        | `"email"`       |
| `utm_source`       | UTM Source                        | `"google"`      |
| `utm_term`         | UTM Term                          | `"search_term"` |

### 10.2 Usage Example

```python
# Example GrowthBook Context Initialization
import growthbook

gb = growthbook.Context(
  api_host="https://your-growthbook-instance.com",
  client_key="your_client_key",
  attributes={
    # Boolean Attributes
    "is_authenticated": True,
    "is_beta": False,
    "is_verified": True,
    "is_creator": False,
    
    # String Attributes
    "country": "vn",
    "os": "android",
    "os_version": "12.0",
    "language": "vi",
    "version": "2.1.0",
    
    # UTM Parameters
    "utm_source": "facebook",
    "utm_medium": "cpc",
    "utm_campaign": "launch_promo"
  }
)
```

## Summary

### Migration Scope
- **980 configuration keys** → 980 GrowthBook feature flags
- **26 unique attributes** → 26 GrowthBook targeting attributes
- **~4 exceptions** → Manual review required
- **99.6% success rate** for automated migration

### Key Deliverables
1. ✅ 980 feature flags in GrowthBook
2. ✅ 26 attributes in GrowthBook
3. ⚠️ ~4 exceptions documented in `except.json`
4. ✅ Migration scripts and documentation
5. ✅ Client integration guide
---
