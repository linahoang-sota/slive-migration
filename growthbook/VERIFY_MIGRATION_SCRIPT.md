# Verify Migration with Test Case Script

## Overview
`verify_migration_with_test_case.py` is a comprehensive verification script that validates GrowthBook feature migration by comparing actual GrowthBook SDK output against expected configuration values.

## Setup

### 1. Configure Environment Variables

Before running the verification script, you must configure your `.env` file:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your GrowthBook settings:

```bash
# Required: GrowthBook API credentials
GROWTHBOOK_API_KEY=your_api_key_here
GROWTHBOOK_PROJECT=your_project_id_here
GROWTHBOOK_OWNER=your_email_here
GROWTHBOOK_API_URL=https://your-growthbook-instance.com/api/v1

# Required: SDK Client Key (get from GrowthBook UI: SDK Connections)
GROWTHBOOK_CLIENT_KEY=your_sdk_key_here

# Required: Environments
GROWTHBOOK_ENVIRONMENTS=production,dev,staging,test

# Optional: Custom workspace root path (defaults to relative paths)
# WORKSPACE_ROOT=/path/to/your/workspace
```

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

## Purpose
This script combines the functionality of `get_growthbook_values.py` and `compare_json_files.py` into a single verification tool with enhanced deep comparison capabilities.

## Features

### 1. GrowthBook Feature Evaluation
- Reads variation IDs from `variations.json`
- Parses variation IDs to GrowthBook attributes
- Evaluates all features using GrowthBook SDK
- Generates complete feature output

### 2. Deep Value Comparison
- **Recursive comparison** at all nesting levels
- Compares dictionaries, lists, and primitive values
- **String normalization**: Treats numeric strings and numbers as equal (e.g., "7" equals 7)
  - GrowthBook stores all values as JSON arrays of strings
  - Integers and floats are converted to strings before comparison
- Reports exact path to differences
- Handles missing keys in either dataset

### 3. Automated Output Generation
- Saves `output.json` (GrowthBook evaluation results)
- Saves `comparison_result.txt` (detailed comparison report)
- Both files saved directly to test case folder

## Usage

```bash
python verify_migration_with_test_case.py <test_case_folder>
```

### Example
```bash
python verify_migration_with_test_case.py ../test_cases/case_1/
```

## Input Requirements

The test case folder must contain:
- **variations.json**: Array of variation IDs (e.g., `["default"]`, `["country=cn", "beta"]`)
- **answer.json**: Expected feature values after migration

## Output Files

Generated in the test case folder:
- **output.json**: Complete GrowthBook feature evaluation results
- **comparison_result.txt**: Detailed comparison report with:
  - Differences found (with exact paths)
  - Missing keys
  - Extra keys
  - Summary statistics
  - Pass/Fail verdict

## Comparison Logic

### Deep Comparison Features
1. **Recursive traversal**: Compares nested objects and arrays at all levels
2. **Path tracking**: Reports exact location of differences (e.g., `FEATURE_NAME[0].subkey`)
3. **String normalization**: GrowthBook stores values as JSON string arrays, so integers/floats are normalized to strings for comparison
4. **Length validation**: Verifies array lengths match
5. **Comprehensive reporting**: Lists all differences, not just first mismatch

### Comparison Categories
- **Matched keys**: Values are identical at all levels
- **Different values**: Values differ (with detailed path and values shown)
- **Missing in GrowthBook**: Keys exist in configuration but not in GrowthBook output
- **Extra in GrowthBook**: Keys exist in GrowthBook but not in configuration (informational only)

## Exit Codes
- **0**: Verification passed (all values match)
- **1**: Verification failed (differences or missing keys found)

## Example Output

```
Test case folder: ../test_cases/case_1/

✓ Loaded 1 variation IDs from variations.json
Evaluating GrowthBook features...
✓ Evaluated 850 features
✓ Loaded 850 expected answers
Comparing results...
✓ Saved GrowthBook output to ../test_cases/case_1/output.json
✓ Saved comparison results to ../test_cases/case_1/comparison_result.txt

================================================================================
MIGRATION VERIFICATION RESULTS
================================================================================

✓ VERIFICATION PASSED - all values match!
```

## Integration

This script is designed to work with:
- **run_all_test_cases.py**: Can be integrated for batch testing
- **Existing test case structure**: Uses standard folder layout
- **CI/CD pipelines**: Exit codes enable automated pass/fail detection

## Advantages Over Separate Scripts

1. **Single execution**: No need to run two separate scripts
2. **Deep comparison**: Goes beyond surface-level comparison
3. **Better error reporting**: Shows exact path to differences
4. **Automated file management**: Saves outputs to correct locations
5. **Cleaner workflow**: One command for complete verification
