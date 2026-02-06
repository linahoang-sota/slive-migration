#!/usr/bin/env python3
"""
Run verify_migration_with_test_case.py for all test cases.

This script runs the verification script on all 50 test case folders
and generates a summary report.

Usage:
    python run_all_verifications.py
"""

import os
import subprocess
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get workspace root (defaults to parent of current script directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", os.path.dirname(SCRIPT_DIR))

TEST_CASES_DIR = os.path.join(WORKSPACE_ROOT, "test_cases")
VERIFY_SCRIPT = os.path.join(SCRIPT_DIR, "verify_migration_with_test_case.py")


def run_verification(test_case_num):
    """
    Run verification for a single test case.
    
    Args:
        test_case_num: Test case number (1-50)
        
    Returns:
        dict: Result with status and details
    """
    test_case_folder = os.path.join(TEST_CASES_DIR, f"case_{test_case_num}")
    
    result = {
        "test_case": test_case_num,
        "status": "unknown",
        "details": {}
    }
    
    # Check if folder exists
    if not os.path.isdir(test_case_folder):
        result["status"] = "skip"
        result["details"]["reason"] = "folder not found"
        return result
    
    # Check if required files exist
    input_file = os.path.join(test_case_folder, "variations.json")
    config_file = os.path.join(test_case_folder, "answer.json")
    
    if not os.path.exists(input_file):
        result["status"] = "skip"
        result["details"]["reason"] = "variations.json not found"
        return result
    
    if not os.path.exists(config_file):
        result["status"] = "skip"
        result["details"]["reason"] = "answer.json not found"
        return result
    
    # Run verification script
    try:
        cmd = [sys.executable, VERIFY_SCRIPT, test_case_folder]
        
        process_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if process_result.returncode == 0:
            result["status"] = "pass"
        else:
            result["status"] = "fail"
            
            # Extract summary from output
            output_lines = process_result.stdout.split('\n')
            for i, line in enumerate(output_lines):
                if 'SUMMARY' in line and i + 6 < len(output_lines):
                    result["details"]["matched"] = output_lines[i + 4].strip()
                    result["details"]["different"] = output_lines[i + 5].strip()
                    result["details"]["missing"] = output_lines[i + 6].strip()
                    break
        
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["details"]["reason"] = "verification timeout"
    except Exception as e:
        result["status"] = "error"
        result["details"]["reason"] = str(e)
    
    return result


def main():
    """Main function"""
    print("="*80)
    print("RUNNING VERIFICATION FOR ALL TEST CASES")
    print("="*80)
    print()
    
    results = []
    
    for i in range(1, 51):
        print(f"[{i}/50] Running verification for case_{i}...", end=" ", flush=True)
        
        result = run_verification(i)
        results.append(result)
        
        status_symbol = {
            "pass": "✓",
            "fail": "✗",
            "skip": "⊘",
            "timeout": "⏱",
            "error": "⚠",
            "unknown": "?"
        }.get(result["status"], "?")
        
        print(f"{status_symbol} {result['status'].upper()}")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    # Count results
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    skipped = sum(1 for r in results if r["status"] == "skip")
    errors = sum(1 for r in results if r["status"] in ["timeout", "error"])
    
    print(f"Total test cases: 50")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"⊘ Skipped: {skipped}")
    print(f"⚠ Errors: {errors}")
    print()
    
    # Show failed cases
    if failed > 0:
        print("Failed test cases:")
        for r in results:
            if r["status"] == "fail":
                print(f"  - case_{r['test_case']}")
                if r["details"]:
                    for key, value in r["details"].items():
                        print(f"    {key}: {value}")
        print()
    
    # Show skipped cases
    if skipped > 0:
        print("Skipped test cases:")
        for r in results:
            if r["status"] == "skip":
                reason = r["details"].get("reason", "unknown")
                print(f"  - case_{r['test_case']}: {reason}")
        print()
    
    # Show error cases
    if errors > 0:
        print("Error/Timeout test cases:")
        for r in results:
            if r["status"] in ["timeout", "error"]:
                reason = r["details"].get("reason", "unknown")
                print(f"  - case_{r['test_case']}: {reason}")
        print()
    
    # Final verdict
    if passed == 50:
        print("🎉 ALL TEST CASES PASSED!")
    elif failed == 0 and errors == 0:
        print(f"✓ All {passed} runnable test cases passed (some skipped)")
    else:
        print(f"✗ {failed + errors} test case(s) failed or had errors")
    
    print()
    
    # Save detailed results
    results_file = os.path.join(TEST_CASES_DIR, "verification_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if failed > 0 or errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
