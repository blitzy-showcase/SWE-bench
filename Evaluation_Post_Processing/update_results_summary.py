#!/usr/bin/env python3
"""
SWE-bench Evaluation Results Analyzer

This script traverses the SWE-bench evaluation logs directory and analyzes
report.json files to count test successes and failures for each instance.
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict


def parse_report_json(file_path):
    """
    Parse a report.json file and extract test counts.
    
    Args:
        file_path (str): Path to the report.json file
        
    Returns:
        dict: Dictionary with instance_id and test counts, or None if parsing fails
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            
        # Handle empty files (known issue from memories)
        if not content:
            print(f"Warning: Empty report.json file at {file_path}")
            return None
            
        data = json.loads(content)
        
        # Extract the instance ID (should be the only key at top level)
        if not data:
            print(f"Warning: Empty JSON data in {file_path}")
            return None
            
        instance_id = list(data.keys())[0]
        instance_data = data[instance_id]
        
        # Extract test status information
        tests_status = instance_data.get('tests_status', {})
        
        # Calculate counts
        pass_to_pass_success = len(tests_status.get('PASS_TO_PASS', {}).get('success', []))
        pass_to_pass_failure = len(tests_status.get('PASS_TO_PASS', {}).get('failure', []))
        pass_to_pass_total = pass_to_pass_success + pass_to_pass_failure
        
        fail_to_pass_success = len(tests_status.get('FAIL_TO_PASS', {}).get('success', []))
        fail_to_pass_failure = len(tests_status.get('FAIL_TO_PASS', {}).get('failure', []))
        fail_to_pass_total = fail_to_pass_success + fail_to_pass_failure
        
        # Get resolved status
        resolved = instance_data.get('resolved', False)
        resolved_status = "✅ resolved" if resolved else "❌ unresolved"
        
        result = {
            'instance_id': instance_id,
            'PASS_TO_PASS': f"{pass_to_pass_success}/{pass_to_pass_total}",
            'FAIL_TO_PASS': f"{fail_to_pass_success}/{fail_to_pass_total}",
            'resolved_status': resolved_status
        }
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Error: JSONDecodeError in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error: Failed to parse {file_path}: {e}")
        return None


def find_report_files(root_dir):
    """
    Recursively find all report.json files in the directory structure.
    
    Args:
        root_dir (str): Root directory to search
        
    Yields:
        str: Path to each report.json file found
    """
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"Error: Directory {root_dir} does not exist")
        return
        
    # Find all report.json files recursively
    for report_file in root_path.rglob('report.json'):
        yield str(report_file)


def analyze_swe_bench_results(logs_dir):
    """
    Analyze all SWE-bench evaluation results and create summary.
    
    Args:
        logs_dir (str): Path to the logs/run_evaluation directory
        
    Returns:
        dict: Summary of all results keyed by instance ID
    """
    results = {}
    total_files = 0
    successful_parses = 0
    failed_parses = 0
    
    print(f"Analyzing SWE-bench results in: {logs_dir}")
    print("=" * 60)
    
    # Find and process all report.json files
    for report_file in find_report_files(logs_dir):
        total_files += 1
        print(f"Processing: {report_file}")
        
        result = parse_report_json(report_file)
        if result:
            instance_id = result['instance_id']
            
            # Create simplified result format
            simplified_result = {
                'PASS_TO_PASS': result['PASS_TO_PASS'],
                'FAIL_TO_PASS': result['FAIL_TO_PASS'],
                'resolved_status': result['resolved_status']
            }
            
            results[instance_id] = simplified_result
            successful_parses += 1
            
            # Print summary for this instance
            print(f"  -> {instance_id}: {result['resolved_status']}")
            print(f"     PASS_TO_PASS: {result['PASS_TO_PASS']}")
            print(f"     FAIL_TO_PASS: {result['FAIL_TO_PASS']}")
        else:
            failed_parses += 1
    
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total report.json files found: {total_files}")
    print(f"  Successfully parsed: {successful_parses}")
    print(f"  Failed to parse: {failed_parses}")
    print(f"  Unique instances: {len(results)}")
    
    return results


def load_existing_results(output_file):
    """
    Load existing results from the JSON file if it exists.
    
    Args:
        output_file (str): Path to the existing results JSON file
        
    Returns:
        dict: Existing results or empty dict if file doesn't exist
    """
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                existing_results = json.load(f)
            print(f"Loaded {len(existing_results)} existing results from {output_file}")
            return existing_results
        else:
            print(f"No existing results file found at {output_file}")
            return {}
    except Exception as e:
        print(f"Warning: Could not load existing results: {e}")
        return {}


def main():
    """Main function to run the analysis."""
    # Default path to the evaluation logs
    logs_dir = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/logs/run_evaluation"
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        logs_dir = sys.argv[1]
    
    # Load existing results first
    output_file = "/Users/jackblundin/Modal_Run_Environment/swe_bench_results_summary.json"
    existing_results = load_existing_results(output_file)
    
    # Run the analysis on current logs
    new_results = analyze_swe_bench_results(logs_dir)
    
    # Merge new results with existing ones (new results take precedence)
    merged_results = existing_results.copy()
    new_instances = 0
    updated_instances = 0
    
    for instance_id, data in new_results.items():
        if instance_id in merged_results:
            updated_instances += 1
            print(f"Updated existing instance: {instance_id}")
        else:
            new_instances += 1
            print(f"Added new instance: {instance_id}")
        merged_results[instance_id] = data
    
    print(f"\nMerge Summary:")
    print(f"  Existing instances: {len(existing_results)}")
    print(f"  New instances found: {new_instances}")
    print(f"  Updated instances: {updated_instances}")
    print(f"  Total instances after merge: {len(merged_results)}")
    
    # Save merged results to JSON file
    try:
        with open(output_file, 'w') as f:
            json.dump(merged_results, f, indent=2, sort_keys=True)
        
        print(f"\nResults saved to: {output_file}")
        print(f"Total instances in final summary: {len(merged_results)}")
        
        # Show a few example results from new instances if any
        if new_instances > 0:
            print(f"\nExample new instances added:")
            count = 0
            for instance_id, data in new_results.items():
                if instance_id not in existing_results:
                    print(f"  {instance_id}: {data['resolved_status']}")
                    print(f"    PASS_TO_PASS: {data['PASS_TO_PASS']}")
                    print(f"    FAIL_TO_PASS: {data['FAIL_TO_PASS']}")
                    count += 1
                    if count >= 3:
                        break
        elif updated_instances > 0:
            print(f"\nExample updated instances:")
            count = 0
            for instance_id, data in new_results.items():
                if instance_id in existing_results:
                    print(f"  {instance_id}: {data['resolved_status']}")
                    print(f"    PASS_TO_PASS: {data['PASS_TO_PASS']}")
                    print(f"    FAIL_TO_PASS: {data['FAIL_TO_PASS']}")
                    count += 1
                    if count >= 3:
                        break
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
