#!/usr/bin/env python3
import os
import difflib
import sys

def compare_files(actual_file, expected_file):
    """Compare two files and return differences."""
    try:
        with open(actual_file, 'r') as f:
            actual_lines = f.readlines()
    except FileNotFoundError:
        return f"Actual file not found: {actual_file}"
    
    try:
        with open(expected_file, 'r') as f:
            expected_lines = f.readlines()
    except FileNotFoundError:
        return f"Expected file not found: {expected_file}"
    
    # Check if files are identical
    if actual_lines == expected_lines:
        return None  # Files match
    
    # Generate detailed diff
    diff = list(difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile=f"Expected ({expected_file})",
        tofile=f"Actual ({actual_file})",
        lineterm='',
        n=3
    ))
    
    return '\n'.join(diff)

def main():
    # Directory containing expected output files
    expected_dir = "pa1-testfiles-1"
    
    # Find all .out files in current directory
    current_dir = "."
    actual_files = [f for f in os.listdir(current_dir) if f.endswith('.out')]
    
    if not actual_files:
        print("No .out files found in current directory")
        sys.exit(1)
    
    print(f"Found {len(actual_files)} .out files to compare\n")
    print("=" * 60)
    
    all_match = True
    results = []
    
    # Sort files for consistent output
    actual_files.sort()
    
    for actual_file in actual_files:
        expected_file = os.path.join(expected_dir, actual_file)
        
        print(f"\nComparing: {actual_file}")
        print("-" * 40)
        
        diff = compare_files(actual_file, expected_file)
        
        if diff is None:
            result = f"✓ MATCH - {actual_file}"
            print(result)
            results.append((actual_file, True, None))
        else:
            result = f"✗ DIFFERENCE - {actual_file}"
            print(result)
            print("\nDifferences found:")
            print(diff)
            results.append((actual_file, False, diff))
            all_match = False
        
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, match, _ in results if match)
    failed = len(results) - passed
    
    print(f"Total files compared: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if all_match:
        print("\n✓ All files match! Your implementation is correct.")
    else:
        print("\n✗ Some files have differences. Review the output above.")
        print("\nFiles with differences:")
        for filename, match, _ in results:
            if not match:
                print(f"  - {filename}")
    
    # Exit with error code if not all match
    sys.exit(0 if all_match else 1)

if __name__ == "__main__":
    main()